"""
Scoring engine for the Vendor Claim Stress Test.

Implements:
  - self-reported downgrade on Distributional Validity (D2) and Leakage Risk (D6)
  - dimension weighting (D2 and D6 double-weighted)
  - independence gate and per-use-case gate (cap verdict at Amber)
  - force-red conditions (D2 or D6 dimension score of zero)
  - verdict banding (Red / Amber / Green)
"""

from dataclasses import dataclass, field
from typing import Optional

from src.data import (
    DIMENSIONS,
    SCALE_SCORES,
    SCALE_LABELS,
    NOT_YET_ASKED_EVIDENCE,
    gate_failed as independence_gate_failed_fn,
)

SELF_REPORTED = "Self-reported by vendor"
DOWNGRADE_DIMENSIONS = {"d2_distributional", "d6_leakage"}


def _downgrade(score: int) -> int:
    """2 -> 1, 1 -> 0, 0 -> 0"""
    return max(0, score - 1)


@dataclass
class QuestionResult:
    dimension_id: str
    dimension_name: str
    question_id: str
    script: str
    score_key: str
    score_label: str
    evidence: str
    raw_score: int          # 0/1/2 as selected
    adjusted_score: float    # after self-report downgrade and minor-weight
    max_score: float         # 2 * minor_weight
    downgraded: bool


@dataclass
class DimensionResult:
    id: str
    number: int
    name: str
    score_weight: int
    eu_ai_act_tag: Optional[str]
    questions: list = field(default_factory=list)  # list[QuestionResult]

    @property
    def any_answered(self) -> bool:
        return len(self.questions) > 0

    @property
    def all_answered(self) -> bool:
        total_qs = len(DIMENSION_QUESTION_COUNT.get(self.id, []))
        return len(self.questions) == total_qs

    @property
    def raw_score_sum(self) -> float:
        return sum(q.adjusted_score for q in self.questions)

    @property
    def max_score_sum(self) -> float:
        return sum(q.max_score for q in self.questions)

    @property
    def weighted_score(self) -> float:
        return self.raw_score_sum * self.score_weight

    @property
    def weighted_max(self) -> float:
        return self.max_score_sum * self.score_weight

    @property
    def pct(self) -> Optional[float]:
        if self.max_score_sum == 0:
            return None
        return round(100 * self.raw_score_sum / self.max_score_sum, 1)


DIMENSION_QUESTION_COUNT = {d["id"]: d["questions"] for d in DIMENSIONS}


@dataclass
class StressTestResult:
    verdict: str  # "RED" | "AMBER" | "GREEN"
    verdict_line: str
    weighted_pct: Optional[float]
    completion_pct: float
    independence_gate_failed: Optional[bool]
    gate_answer: Optional[str]
    dimension_3_gate_failed: bool
    force_red: bool
    force_red_reasons: list
    dimensions: list  # list[DimensionResult]
    vendor_declined: list  # list[QuestionResult]: asked, vendor wouldn't say
    not_yet_asked: list    # list[QuestionResult]: buyer hasn't asked / isn't sure
    inadequate: list  # list[QuestionResult] where score_key == inadequate
    followup_targets: list  # list[(dimension, QuestionResult)] scored amber/red


VERDICT_MESSAGES = {
    "RED": "Do not proceed without further evidence",
    "AMBER": "Proceed with conditions",
    "GREEN": "Proceed with confidence",
}


def score_answer(dimension: dict, question: dict, answer: dict) -> QuestionResult:
    """answer = {"score_key": "adequate"|"inadequate"|"withheld", "evidence": str}"""
    score_key = answer["score_key"]
    evidence = answer.get("evidence", NOT_YET_ASKED_EVIDENCE)
    raw_score = SCALE_SCORES[score_key]
    minor_weight = question.get("minor_weight", 1.0)

    downgraded = False
    effective_score = raw_score
    if dimension["id"] in DOWNGRADE_DIMENSIONS and evidence == SELF_REPORTED:
        new_score = _downgrade(raw_score)
        downgraded = new_score != raw_score
        effective_score = new_score

    return QuestionResult(
        dimension_id=dimension["id"],
        dimension_name=dimension["name"],
        question_id=question["id"],
        script=question["script"],
        score_key=score_key,
        score_label=SCALE_LABELS[score_key],
        evidence=evidence,
        raw_score=raw_score,
        adjusted_score=effective_score * minor_weight,
        max_score=2 * minor_weight,
        downgraded=downgraded,
    )


def compute_dimension_result(dimension: dict, dim_answers: dict) -> DimensionResult:
    result = DimensionResult(
        id=dimension["id"],
        number=dimension["number"],
        name=dimension["name"],
        score_weight=dimension["score_weight"],
        eu_ai_act_tag=dimension.get("eu_ai_act_tag"),
    )
    for question in dimension["questions"]:
        answer = dim_answers.get(question["id"])
        if answer is None:
            continue
        result.questions.append(score_answer(dimension, question, answer))
    return result


def compute_result(
    answers: dict,
    gate_answer: Optional[str],
    multi_use_case: Optional[bool],
) -> StressTestResult:
    """
    answers: {dimension_id: {question_id: {"score_key":..., "evidence":...}}}
    gate_answer: one of the GATE_QUESTION option keys, or None if unanswered
    multi_use_case: True/False/None (None = not yet answered)
    """
    dim_results = []
    vendor_declined = []
    not_yet_asked = []
    inadequate = []
    followup_targets = []

    weighted_score_total = 0.0
    weighted_max_total = 0.0
    answered_questions = 0

    d3_result = None

    for dimension in DIMENSIONS:
        dim_answers = answers.get(dimension["id"], {})
        dr = compute_dimension_result(dimension, dim_answers)
        dim_results.append(dr)
        if dimension["id"] == "d3_percase":
            d3_result = dr

        if dr.any_answered:
            weighted_score_total += dr.weighted_score
            weighted_max_total += dr.weighted_max

        for q in dr.questions:
            answered_questions += 1
            if q.score_key == "withheld":
                if q.evidence == NOT_YET_ASKED_EVIDENCE:
                    not_yet_asked.append(q)
                else:
                    vendor_declined.append(q)
            elif q.score_key == "inadequate":
                inadequate.append(q)
            if q.score_key in ("withheld", "inadequate"):
                followup_targets.append(q)

    # +1 for the Evaluator Independence gate question — it's asked "before
    # anything else" and is not part of any dimension, but skipping it is
    # still an outstanding item, not something "100%" should paper over.
    total_questions = sum(len(d["questions"]) for d in DIMENSIONS) + 1
    answered_questions_all = answered_questions + (1 if gate_answer is not None else 0)
    completion_pct = round(100 * answered_questions_all / total_questions, 1)

    weighted_pct = None
    if weighted_max_total > 0:
        weighted_pct = round(100 * weighted_score_total / weighted_max_total, 1)

    # Gates
    independence_failed = (
        independence_gate_failed_fn(gate_answer) if gate_answer else None
    )

    dimension_3_gate_failed = False
    if d3_result is not None and d3_result.any_answered:
        if multi_use_case is None:
            # Reached this dimension but never said whether it's multi-use-case —
            # treat as outstanding, not as a silent "single use case" pass.
            dimension_3_gate_failed = True
        elif multi_use_case:
            d3_q1 = next((q for q in d3_result.questions if q.question_id == "d3_q1"), None)
            if d3_q1 is not None and d3_q1.raw_score < 2:
                dimension_3_gate_failed = True

    force_red = False
    force_red_reasons = []
    d2_result = next((d for d in dim_results if d.id == "d2_distributional"), None)
    d6_result = next((d for d in dim_results if d.id == "d6_leakage"), None)
    if d2_result is not None and d2_result.any_answered and d2_result.raw_score_sum == 0:
        force_red = True
        force_red_reasons.append(
            "Distributional Validity scored zero — the 'unseen' data claim and "
            "subgroup breakdown are both unsupported."
        )
    if d6_result is not None and d6_result.any_answered and d6_result.raw_score_sum == 0:
        force_red = True
        force_red_reasons.append(
            "Leakage Risk scored zero — there is no evidence separating training "
            "and test data."
        )

    # Cap the verdict unless independence has been explicitly confirmed
    # (internal_separate / independent_third_party). An unanswered gate
    # (independence_failed is None) is not a pass — it's exactly the same
    # "we don't actually know" situation as an explicit "dont_know" answer,
    # and must not let a verdict reach GREEN on missing information.
    gate_cap_applies = independence_failed is not False or dimension_3_gate_failed

    # Verdict banding
    if force_red:
        verdict = "RED"
    elif weighted_pct is not None and weighted_pct < 60:
        verdict = "RED"
    elif gate_cap_applies:
        verdict = "AMBER"
    elif weighted_pct is not None and 60 <= weighted_pct < 85:
        verdict = "AMBER"
    elif weighted_pct is not None and weighted_pct >= 85 and not gate_cap_applies:
        verdict = "GREEN"
    else:
        # Not enough data yet to land on a percentage-driven band
        verdict = "AMBER" if weighted_pct is not None else "RED"

    return StressTestResult(
        verdict=verdict,
        verdict_line=VERDICT_MESSAGES[verdict],
        weighted_pct=weighted_pct,
        completion_pct=completion_pct,
        independence_gate_failed=independence_failed,
        gate_answer=gate_answer,
        dimension_3_gate_failed=dimension_3_gate_failed,
        force_red=force_red,
        force_red_reasons=force_red_reasons,
        dimensions=dim_results,
        vendor_declined=vendor_declined,
        not_yet_asked=not_yet_asked,
        inadequate=inadequate,
        followup_targets=followup_targets,
    )
