"""
Static content for the Vendor Claim Stress Test: dimensions, questions,
scoring scale, follow-up question templates, and the worked example.
"""

# --- Answer scale -----------------------------------------------------------

SCALE_OPTIONS = [
    ("adequate", "Provided & adequate", 2),
    ("inadequate", "Provided & inadequate", 1),
    ("withheld", "Not provided / don't know", 0),
]
SCALE_LABELS = {key: label for key, label, _ in SCALE_OPTIONS}
SCALE_SCORES = {key: score for key, _, score in SCALE_OPTIONS}

EVIDENCE_TAGS = [
    "Self-reported by vendor",
    "Documented & verifiable",
    "Not applicable",
]

# --- Global gate question ----------------------------------------------------

GATE_QUESTION = {
    "id": "gate_independence",
    "title": "Who checked their own homework?",
    "script": (
        "Ask the vendor: who ran this evaluation — their own model team, "
        "an internal-but-separate team, or an independent third party?"
    ),
    "options": [
        ("same_team", "Same team"),
        ("internal_separate", "Internal-separate team"),
        ("independent_third_party", "Independent third party"),
        ("dont_know", "Don't know"),
    ],
}


def gate_failed(gate_answer: str) -> bool:
    return gate_answer in ("same_team", "dont_know")


# --- Seven dimensions --------------------------------------------------------
# Each question: id, script (read-to-vendor phrasing), minor_weight (0.5 or 1.0)
# Each dimension: id, number (1-7), name, eu_ai_act_tag, score_weight (1 or 2), questions

DIMENSIONS = [
    {
        "id": "d1_provenance",
        "number": 1,
        "name": "Test Set Provenance",
        "eu_ai_act_tag": "Art. 15",
        "score_weight": 1,
        "questions": [
            {
                "id": "d1_q1",
                "script": "Ask: was your test data set aside before training started, or put together afterwards?",
                "minor_weight": 1.0,
            },
        ],
    },
    {
        "id": "d2_distributional",
        "number": 2,
        "name": "Distributional Validity",
        "eu_ai_act_tag": "Art. 15",
        "score_weight": 2,
        "questions": [
            {
                "id": "d2_q1",
                "script": "Ask: was your 'unseen' test data actually from different conditions, or just a different slice of the same environment?",
                "minor_weight": 1.0,
            },
            {
                "id": "d2_q2",
                "script": "Ask: did they break results down by site/subgroup/condition, or just give you one overall number?",
                "minor_weight": 1.0,
            },
        ],
    },
    {
        "id": "d3_percase",
        "number": 3,
        "name": "Per-Use-Case & Cost-Weighted Breakdown",
        "gate_dimension": True,
        "eu_ai_act_tag": None,
        "score_weight": 1,
        "questions": [
            {
                "id": "d3_q1",
                "script": "Ask: if this covers multiple use cases, do they report performance per use case, or just a blended average?",
                "minor_weight": 1.0,
            },
            {
                "id": "d3_q2",
                "script": (
                    "Ask: is a false positive or a false negative more costly to your business — "
                    "and does their evaluation reflect that, or is it one blended number that hides "
                    "which one you're actually exposed to?"
                ),
                "minor_weight": 1.0,
            },
        ],
    },
    {
        "id": "d4_temporal",
        "number": 4,
        "name": "Temporal Representativeness",
        "eu_ai_act_tag": None,
        "score_weight": 1,
        "questions": [
            {
                "id": "d4_q1",
                "script": "Ask: was the test data collected under conditions like what you'll actually deploy into, or is it stale/unrepresentative?",
                "minor_weight": 1.0,
            },
            {
                "id": "d4_q2",
                "script": "Ask: are these static test cases, or do they reflect real-world conditions changing over time?",
                "minor_weight": 1.0,
            },
        ],
    },
    {
        "id": "d5_metric",
        "number": 5,
        "name": "Metric Selection, Baseline & Threshold Integrity",
        "eu_ai_act_tag": "Art. 15",
        "score_weight": 1,
        "questions": [
            {
                "id": "d5_q1",
                "script": (
                    "Ask: does the metric they're showing you actually match the business outcome "
                    "you need — or did they pick a metric because it looks good, not because it's "
                    "what you care about?"
                ),
                "minor_weight": 1.0,
            },
            {
                "id": "d5_q2",
                "script": "Ask: was the pass/fail threshold agreed before they saw the results, or chosen afterwards to fit the number they got?",
                "minor_weight": 1.0,
            },
            {
                "id": "d5_q3",
                "script": "Ask: did they compare against a baseline or simplest-possible-approach, or is this number presented with nothing to compare it to?",
                "minor_weight": 1.0,
            },
            {
                "id": "d5_q4",
                "script": "Ask: did they test against tricky edge cases, or only the easy ones?",
                "minor_weight": 0.5,
            },
        ],
    },
    {
        "id": "d6_leakage",
        "number": 6,
        "name": "Leakage Risk",
        "eu_ai_act_tag": None,
        "score_weight": 2,
        "questions": [
            {
                "id": "d6_q1",
                "script": "Ask: is there any overlap between the data they trained on and the data they tested on — same stores, same time period, same source?",
                "minor_weight": 1.0,
            },
            {
                "id": "d6_q2",
                "script": "Ask: did they check for and remove near-duplicate records between training and test data?",
                "minor_weight": 1.0,
            },
        ],
    },
    {
        "id": "d7_transparency",
        "number": 7,
        "name": "Reporting Transparency",
        "eu_ai_act_tag": None,
        "score_weight": 1,
        "questions": [
            {
                "id": "d7_q1",
                "script": "Ask: did they show you where it failed, or only where it succeeded?",
                "minor_weight": 1.0,
            },
            {
                "id": "d7_q2",
                "script": "Ask: is there a written limitations section, or is this presented as flawless?",
                "minor_weight": 1.0,
            },
            {
                "id": "d7_q3",
                "script": "Ask: is there enough detail here that an independent person could rerun this evaluation and get the same answer?",
                "minor_weight": 1.0,
            },
        ],
    },
]

DIMENSION_BY_ID = {d["id"]: d for d in DIMENSIONS}
ALL_QUESTION_IDS = [q["id"] for d in DIMENSIONS for q in d["questions"]]
TOTAL_QUESTIONS = len(ALL_QUESTION_IDS)

GLOBAL_ART9_TAG = "Art. 9"  # global independence gate maps to Art. 9

# --- Follow-up question templates (sent to vendor when scored Amber/Red) ----
# Keyed by question id — these are slightly reframed as direct requests for evidence.

FOLLOWUP_TEMPLATES = {
    "gate_independence": (
        "Please confirm in writing who executed this evaluation, and if it was not an "
        "independent third party, provide the reasoning for why we should trust an "
        "internally-run result."
    ),
    "d1_q1": (
        "Please provide documentation showing the test set was defined and frozen "
        "before training began (e.g. a dated data-split manifest)."
    ),
    "d2_q1": (
        "Please describe precisely what differs between your 'seen' and 'unseen' test "
        "data (site, time period, customer, hardware) and provide evidence of that "
        "difference."
    ),
    "d2_q2": (
        "Please provide a breakdown of results by site, subgroup, or condition — not "
        "just a single blended number."
    ),
    "d3_q1": (
        "Please provide per-use-case performance figures, not a blended average across "
        "use cases."
    ),
    "d3_q2": (
        "Please tell us your assumed cost ratio of false positives to false negatives, "
        "and provide a breakdown showing which error type this evaluation is actually "
        "exposed to."
    ),
    "d4_q1": (
        "Please confirm when and under what conditions the test data was collected, and "
        "how that compares to our deployment environment."
    ),
    "d4_q2": (
        "Please explain how the evaluation accounts for real-world drift over time, or "
        "provide a plan for ongoing re-evaluation."
    ),
    "d5_q1": (
        "Please explain why this metric was chosen and how it maps to the business "
        "outcome we care about."
    ),
    "d5_q2": (
        "Please provide evidence that the pass/fail threshold was set before results "
        "were seen (e.g. a dated evaluation protocol)."
    ),
    "d5_q3": (
        "Please provide a comparison against a simple baseline or the next-best "
        "alternative approach."
    ),
    "d5_q4": (
        "Please provide results on adversarial or edge-case examples, not only "
        "typical/easy cases."
    ),
    "d6_q1": (
        "Please confirm there is no overlap in stores, time period, or source between "
        "training and test data, with supporting evidence."
    ),
    "d6_q2": (
        "Please describe the deduplication process used to remove near-duplicate "
        "records between training and test data."
    ),
    "d7_q1": (
        "Please share the failure cases and error analysis, not only successful "
        "examples."
    ),
    "d7_q2": (
        "Please provide a written limitations section covering where this evaluation "
        "does not apply."
    ),
    "d7_q3": (
        "Please provide enough methodological detail (data sources, splits, code, "
        "parameters) that an independent party could reproduce this evaluation."
    ),
}

# --- Worked example: anonymised real retail AI bake-off scenario, scores RED ---

WORKED_EXAMPLE = {
    "gate_answer": "same_team",
    "multi_use_case": True,
    "answers": {
        # dimension_id -> {question_id: {"score_key": ..., "evidence": ...}}
        "d1_provenance": {
            "d1_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
        },
        "d2_distributional": {
            "d2_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d2_q2": {"score_key": "withheld", "evidence": "Self-reported by vendor"},
        },
        "d3_percase": {
            "d3_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d3_q2": {"score_key": "withheld", "evidence": "Not applicable"},
        },
        "d4_temporal": {
            "d4_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d4_q2": {"score_key": "withheld", "evidence": "Not applicable"},
        },
        "d5_metric": {
            "d5_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d5_q2": {"score_key": "withheld", "evidence": "Not applicable"},
            "d5_q3": {"score_key": "withheld", "evidence": "Not applicable"},
            "d5_q4": {"score_key": "withheld", "evidence": "Not applicable"},
        },
        "d6_leakage": {
            "d6_q1": {"score_key": "withheld", "evidence": "Self-reported by vendor"},
            "d6_q2": {"score_key": "withheld", "evidence": "Not applicable"},
        },
        "d7_transparency": {
            "d7_q1": {"score_key": "withheld", "evidence": "Not applicable"},
            "d7_q2": {"score_key": "withheld", "evidence": "Not applicable"},
            "d7_q3": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
        },
    },
    "narrative_context": (
        "Retail AI bake-off: vendor reported 48% blended precision vs 17% on one "
        "specific use case, near-identical seen/unseen performance curves, test data "
        "drawn from a single store, no baseline comparison offered, and the evaluation "
        "was run and self-reported by the vendor's own model team."
    ),
}
