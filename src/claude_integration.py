"""
Claude API integration for the Vendor Claim Stress Test.

Mirrors the Claude API integration pattern used by the CA AI Governance
Toolkit's other tools (Model Card Generator's gap-analysis call, Annotation
Brief Builder): a single Messages API call with a strict system prompt that
forbids invented findings and requires plain-English, evidence-grounded
output.
"""

import os

import anthropic
import streamlit as st

MODEL = "claude-sonnet-4-5"

SYSTEM_PROMPT = """You are an assistant embedded in the "Vendor Claim Stress Test" tool, \
part of the CA AI Governance Toolkit. Buyers use this tool to pressure-test an AI \
vendor's evaluation claims before purchase. You are shown a buyer's answers to a \
structured questionnaire about a vendor's evaluation evidence, plus the tool's own \
computed scores and verdict.

Your job: write a short narrative (150-250 words) explaining what this evaluation \
ACTUALLY tells the buyer versus what it is being PRESENTED as telling them.

Hard rules:
1. Never invent findings, numbers, or vendor behavior that are not implied by the \
   specific answers given. If the buyer marked something "don't know," say that \
   information is missing — do not guess what the true answer might be.
2. Do not assess whether the underlying AI model is good, accurate, or fit for \
   purpose. You are assessing whether the EVIDENCE the buyer has been shown is \
   honest and relevant to their use case — nothing else.
3. Write in plain English. No ML jargon (no "distribution shift," "data leakage," \
   "false positive rate" without explanation, etc.) — explain any technical concept \
   in a sentence a non-technical buyer would understand.
4. Explicitly reference the specific dimensions (by their plain name, e.g. "the \
   leakage risk question" or "the independence of who ran this evaluation") that \
   drove the verdict. Do not give generic commentary that could apply to any vendor.
5. Do not discuss pricing, contracts, vendor viability, or whether the buyer picked \
   the right use case — that is explicitly out of scope for this tool.
6. End with a one-sentence statement of what the buyer's single biggest exposure is, \
   grounded in the specific answers given.

Output only the narrative text. No headers, no bullet points, no preamble."""


def _get_api_key() -> str | None:
    if "ANTHROPIC_API_KEY" in os.environ:
        return os.environ["ANTHROPIC_API_KEY"]
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


def _build_user_prompt(result, context_note: str = "") -> str:
    lines = []
    lines.append(f"VERDICT: {result.verdict} — {result.verdict_line}")
    if result.weighted_pct is not None:
        lines.append(f"Weighted evidence score: {result.weighted_pct}%")
    lines.append(f"Questionnaire completion: {result.completion_pct}%")
    lines.append("")
    lines.append("EVALUATOR INDEPENDENCE (asked first, separately from the 7 dimensions):")
    lines.append(f"  Answer: {result.gate_answer or 'not answered'}")
    lines.append(f"  Independence gate failed: {bool(result.independence_gate_failed)}")
    lines.append("")
    if result.force_red_reasons:
        lines.append("FORCED-RED REASONS:")
        for reason in result.force_red_reasons:
            lines.append(f"  - {reason}")
        lines.append("")
    if result.dimension_3_gate_failed:
        lines.append(
            "GATE: Multiple use cases are covered but only a blended average was "
            "provided (no per-use-case breakdown) — verdict capped at Amber.\n"
        )

    lines.append("DIMENSION-BY-DIMENSION ANSWERS:")
    for dim in result.dimensions:
        if not dim.any_answered:
            lines.append(f"  [{dim.number}] {dim.name}: not answered")
            continue
        pct = dim.pct
        lines.append(
            f"  [{dim.number}] {dim.name} (weight x{dim.score_weight}, "
            f"score {dim.raw_score_sum}/{dim.max_score_sum}"
            + (f", {pct}%" if pct is not None else "")
            + "):"
        )
        for q in dim.questions:
            downgrade_note = " [downgraded: self-reported]" if q.downgraded else ""
            lines.append(
                f"    - \"{q.script}\" -> {q.score_label} "
                f"(evidence: {q.evidence}){downgrade_note}"
            )
    if context_note:
        lines.append("")
        lines.append("ADDITIONAL CONTEXT PROVIDED BY THE BUYER:")
        lines.append(f"  {context_note}")

    lines.append("")
    lines.append(
        "Write the 150-250 word narrative now, grounded only in the specific "
        "answers above."
    )
    return "\n".join(lines)


def generate_narrative(result, context_note: str = "") -> str:
    """Call Claude to generate the grounded narrative. Returns the narrative text,
    or raises RuntimeError with a user-facing message on failure."""
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "No Anthropic API key configured. Set the ANTHROPIC_API_KEY environment "
            "variable or add it to Streamlit secrets to enable the narrative summary."
        )

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = _build_user_prompt(result, context_note)

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text_parts = [block.text for block in response.content if block.type == "text"]
    narrative = "\n".join(text_parts).strip()
    if not narrative:
        raise RuntimeError("Claude returned an empty response. Please try again.")
    return narrative
