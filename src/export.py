"""
Export the Vendor Claim Stress Test output (flags, narrative, technical
scorecard) as a Markdown report or a PDF, formatted for the buyer to forward
internally.
"""

from datetime import datetime
from io import BytesIO

from src.data import GLOBAL_ART9_TAG


def build_markdown_report(result, narrative: str, vendor_name: str = "") -> str:
    lines = []
    title = f"Vendor Claim Stress Test — {vendor_name}" if vendor_name else "Vendor Claim Stress Test"
    lines.append(f"# {title}")
    lines.append(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")
    lines.append(f"## Verdict: {result.verdict} — {result.verdict_line}")
    if result.weighted_pct is not None:
        lines.append(f"Weighted evidence score: **{result.weighted_pct}%** "
                      f"(wizard {result.completion_pct}% answered)")
        lines.append(
            "_Wizard-answered means every question has a recorded response — "
            "including 'I haven't asked yet.' It is not a measure of how much "
            "evidence you actually have; see Flags below for outstanding gaps._"
        )
    lines.append("")
    lines.append(
        "> This tool checks whether the evidence you've been shown is honest and "
        "relevant. It does not assess pricing, contracts, vendor viability, or "
        "whether you've picked the right use case."
    )
    lines.append("")

    # --- Evaluator independence ---
    lines.append("## Evaluator Independence")
    answer_map = {
        "same_team": "Same team",
        "internal_separate": "Internal-separate team",
        "independent_third_party": "Independent third party",
        "dont_know": "Don't know",
    }
    lines.append(f"- Answer: **{answer_map.get(result.gate_answer, 'Not answered')}**")
    lines.append(f"- Gate failed: **{bool(result.independence_gate_failed)}** "
                 f"(tagged EU AI Act {GLOBAL_ART9_TAG})")
    lines.append(
        "- Why it matters: an evaluation run and reported by the model's own "
        "team has an inherent conflict of interest — it does not tell you "
        "anything about how the model performs under scrutiny it didn't design "
        "for itself."
    )
    lines.append("")

    # --- Section 4: Flag lists ---
    lines.append("## Flags")
    lines.append("### Still need to ask — not yet answered")
    lines.append(
        "_You haven't gotten this from the vendor yet, or aren't sure how to "
        "judge it. This isn't a mark against the vendor — it's your to-do list. "
        "Use the questions below next time you speak with them._"
    )
    if result.not_yet_asked:
        for q in result.not_yet_asked:
            lines.append(f"- **[{q.dimension_name}]** {q.script}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("### Vendor wouldn't answer")
    lines.append(
        "_The vendor was asked directly and did not provide this. Treat this "
        "as a signal about their transparency, not just a gap in your own "
        "homework._"
    )
    if result.vendor_declined:
        for q in result.vendor_declined:
            lines.append(f"- **[{q.dimension_name}]** {q.script}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append("### Information provided and inadequate")
    if result.inadequate:
        for q in result.inadequate:
            lines.append(f"- **[{q.dimension_name}]** {q.script} _(evidence: {q.evidence})_")
    else:
        lines.append("- None.")
    lines.append("")

    if result.force_red_reasons:
        lines.append("### Forced-red reasons")
        for reason in result.force_red_reasons:
            lines.append(f"- {reason}")
        lines.append("")

    if result.dimension_3_gate_failed:
        lines.append(
            "### Gate: multi-use-case blended reporting\n"
            "This evaluation covers multiple use cases but only a blended "
            "average was provided — the verdict is capped at Amber until a "
            "per-use-case breakdown is supplied.\n"
        )

    # --- Send-to-vendor questions ---
    from src.data import FOLLOWUP_TEMPLATES

    lines.append("## Send these questions to your vendor")
    if result.independence_gate_failed:
        lines.append(f"- {FOLLOWUP_TEMPLATES['gate_independence']}")
    if result.followup_targets:
        for q in result.followup_targets:
            template = FOLLOWUP_TEMPLATES.get(q.question_id)
            if template:
                lines.append(f"- **[{q.dimension_name}]** {template}")
    if not result.independence_gate_failed and not result.followup_targets:
        lines.append("- No outstanding follow-up questions — every dimension scored adequate.")
    lines.append("")

    # --- Section 5: Narrative ---
    lines.append("## What this evaluation actually tells you")
    lines.append(narrative if narrative else "_Narrative not generated._")
    lines.append("")

    # --- Section 6: Technical scorecard appendix ---
    lines.append("## Technical scorecard (appendix)")
    for dim in result.dimensions:
        weight_note = f"×{dim.score_weight}" if dim.score_weight != 1 else ""
        tag = f" — EU AI Act {dim.eu_ai_act_tag}" if dim.eu_ai_act_tag else ""
        lines.append(f"### {dim.number}. {dim.name} {weight_note}{tag}")
        if not dim.any_answered:
            lines.append("_Not answered._")
            lines.append("")
            continue
        line = f"Raw score: {dim.raw_score_sum:g}/{dim.max_score_sum:g}"
        if dim.pct is not None:
            line += f" ({dim.pct}%)"
        if dim.score_weight != 1:
            line += (
                f" · weighted contribution to overall score: "
                f"{dim.weighted_score:g}/{dim.weighted_max:g} (raw ×{dim.score_weight})"
            )
        lines.append(line)
        lines.append("")
        lines.append("| Question | Answer | Evidence | Score |")
        lines.append("|---|---|---|---|")
        for q in dim.questions:
            downgrade = " (downgraded — self-reported)" if q.downgraded else ""
            lines.append(
                f"| {q.script} | {q.score_label} | {q.evidence} | "
                f"{q.adjusted_score}/{q.max_score}{downgrade} |"
            )
        lines.append("")

    lines.append("---")
    lines.append(
        "_Generated by the Vendor Claim Stress Test — CA AI Governance Toolkit._"
    )
    return "\n".join(lines)


def build_pdf_report(result, narrative: str, vendor_name: str = "") -> bytes:
    """Render a simple PDF version of the report using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def h1(text):
        pdf.set_font("Helvetica", "B", 16)
        pdf.multi_cell(0, 10, text)
        pdf.ln(2)

    def h2(text):
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 8, text)
        pdf.ln(1)

    def body(text):
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, text)
        pdf.ln(1)

    def _clean(text: str) -> str:
        # fpdf2's core fonts are latin-1 only; sanitize smart punctuation etc.
        replacements = {
            "‘": "'", "’": "'", "“": '"', "”": '"',
            "–": "-", "—": "-", "…": "...",
        }
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        return text.encode("latin-1", "replace").decode("latin-1")

    title = f"Vendor Claim Stress Test - {vendor_name}" if vendor_name else "Vendor Claim Stress Test"
    h1(_clean(title))
    body(_clean(f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"))

    h2(_clean(f"Verdict: {result.verdict} - {result.verdict_line}"))
    if result.weighted_pct is not None:
        body(_clean(f"Weighted evidence score: {result.weighted_pct}% "
                     f"(wizard {result.completion_pct}% answered)"))
        body(_clean(
            "Wizard-answered means every question has a recorded response - "
            "including 'I haven't asked yet.' It is not a measure of how much "
            "evidence you actually have; see Flags below for outstanding gaps."
        ))

    answer_map = {
        "same_team": "Same team",
        "internal_separate": "Internal-separate team",
        "independent_third_party": "Independent third party",
        "dont_know": "Don't know",
    }
    h2("Evaluator Independence")
    body(_clean(f"Answer: {answer_map.get(result.gate_answer, 'Not answered')}"))
    body(_clean(
        f"Gate failed: {bool(result.independence_gate_failed)} "
        f"(tagged EU AI Act {GLOBAL_ART9_TAG})"
    ))
    body(_clean(
        "Why it matters: an evaluation run and reported by the model's own team "
        "has an inherent conflict of interest - it does not tell you anything "
        "about how the model performs under scrutiny it didn't design for itself."
    ))

    h2("Flags")
    body("Still need to ask - not yet answered:")
    body(_clean(
        "(Not a mark against the vendor - this is the buyer's own to-do list.)"
    ))
    if result.not_yet_asked:
        for q in result.not_yet_asked:
            body(_clean(f"  - [{q.dimension_name}] {q.script}"))
    else:
        body("  - None.")
    body("Vendor wouldn't answer:")
    body(_clean(
        "(The vendor was asked directly and did not provide this.)"
    ))
    if result.vendor_declined:
        for q in result.vendor_declined:
            body(_clean(f"  - [{q.dimension_name}] {q.script}"))
    else:
        body("  - None.")
    body("Information provided and inadequate:")
    if result.inadequate:
        for q in result.inadequate:
            body(_clean(f"  - [{q.dimension_name}] {q.script} (evidence: {q.evidence})"))
    else:
        body("  - None.")

    from src.data import FOLLOWUP_TEMPLATES

    h2("Send these questions to your vendor")
    if result.independence_gate_failed:
        body(_clean(f"- {FOLLOWUP_TEMPLATES['gate_independence']}"))
    for q in result.followup_targets:
        template = FOLLOWUP_TEMPLATES.get(q.question_id)
        if template:
            body(_clean(f"- [{q.dimension_name}] {template}"))

    h2("What this evaluation actually tells you")
    body(_clean(narrative or "Narrative not generated."))

    h2("Technical scorecard (appendix)")
    for dim in result.dimensions:
        tag = f" - EU AI Act {dim.eu_ai_act_tag}" if dim.eu_ai_act_tag else ""
        h2(_clean(f"{dim.number}. {dim.name} (x{dim.score_weight}){tag}"))
        if not dim.any_answered:
            body("Not answered.")
            continue
        score_line = f"Raw score: {dim.raw_score_sum:g}/{dim.max_score_sum:g}"
        if dim.score_weight != 1:
            score_line += (
                f" - weighted contribution to overall score: "
                f"{dim.weighted_score:g}/{dim.weighted_max:g} (raw x{dim.score_weight})"
            )
        body(_clean(score_line))
        for q in dim.questions:
            downgrade = " (downgraded - self-reported)" if q.downgraded else ""
            body(_clean(
                f"  - {q.script}\n    Answer: {q.score_label} | Evidence: "
                f"{q.evidence} | Score: {q.adjusted_score}/{q.max_score}{downgrade}"
            ))

    buf = BytesIO()
    pdf_bytes = pdf.output()
    buf.write(bytes(pdf_bytes))
    buf.seek(0)
    return buf.getvalue()
