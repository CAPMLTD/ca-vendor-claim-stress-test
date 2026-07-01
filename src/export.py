"""
Export the Vendor Claim Stress Test output (flags, narrative, technical
scorecard) as a Markdown report or a PDF, styled to match the app's own
CAPMLTD branding and traffic-light treatment so the report doesn't feel like
a different tool than the one that produced it.
"""

from datetime import datetime
from io import BytesIO

from src.data import GLOBAL_ART9_TAG, FOLLOWUP_TEMPLATES

GATE_ANSWER_LABELS = {
    "same_team": "Same team",
    "internal_separate": "Internal-separate team",
    "independent_third_party": "Independent third party",
    "dont_know": "Don't know",
}

VERDICT_EMOJI = {"RED": "🔴", "AMBER": "🟡", "GREEN": "🟢"}


# --------------------------------------------------------------------------- #
# Markdown report
# --------------------------------------------------------------------------- #

def build_markdown_report(result, narrative: str, vendor_name: str = "") -> str:
    lines = []
    title = f"Vendor Claim Stress Test — {vendor_name}" if vendor_name else "Vendor Claim Stress Test"
    emoji = VERDICT_EMOJI.get(result.verdict, "")

    lines.append(f"# 🚦 {title}")
    lines.append(
        "*CA Project Management Services Ltd (CAPMLTD) · caprojectmgmt.com*"
    )
    lines.append(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_")
    lines.append("")
    lines.append(
        "> **Scope:** This tool checks whether the evidence you've been shown "
        "is honest and relevant. It does not assess pricing, contracts, vendor "
        "viability, or whether you've picked the right use case."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- 1. Verdict ---
    lines.append(f"## {emoji} Verdict: {result.verdict} — {result.verdict_line}")
    lines.append("")
    if result.weighted_pct is not None:
        lines.append(f"**Weighted evidence score:** {result.weighted_pct}%")
        lines.append(
            f"_(wizard {result.completion_pct}% answered — this means every "
            "question has a recorded response, including 'I haven't asked "
            "yet.' It is not a measure of how much evidence you actually "
            "have; see Flags below for outstanding gaps.)_"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- 2. Evaluator independence ---
    lines.append("## 🔎 Evaluator Independence")
    if result.independence_gate_failed is None:
        gate_pill = "🟡 NOT YET ANSWERED"
    elif result.independence_gate_failed:
        gate_pill = "🔴 GATE FAILED"
    else:
        gate_pill = "🟢 PASSED"
    lines.append(
        f"**Who ran this evaluation:** {GATE_ANSWER_LABELS.get(result.gate_answer, 'Not answered')} "
        f"— {gate_pill}"
    )
    lines.append(
        f"_(tagged EU AI Act {GLOBAL_ART9_TAG})_"
    )
    lines.append("")
    lines.append(
        "> Why it matters: an evaluation run and reported by the model's own "
        "team has an inherent conflict of interest — it does not tell you "
        "anything about how the model performs under scrutiny it didn't "
        "design for itself."
    )
    lines.append("")

    if result.dimension_3_gate_failed:
        lines.append(
            "> ⚠️ **Gate: blended-only reporting across multiple use cases.** "
            "This evaluation covers more than one use case but only a "
            "blended average was provided — the verdict is capped at Amber "
            "until a per-use-case breakdown is supplied."
        )
        lines.append("")
    if result.force_red_reasons:
        for reason in result.force_red_reasons:
            lines.append(f"> 🚫 **Forced Red:** {reason}")
        lines.append("")

    lines.append("---")
    lines.append("")

    # --- 3. Send these questions to your vendor ---
    lines.append("## 📤 Send these questions to your vendor")
    any_followups = False
    if result.independence_gate_failed is not False:
        any_followups = True
        lines.append(f"- {FOLLOWUP_TEMPLATES['gate_independence']}")
    for q in result.followup_targets:
        template = FOLLOWUP_TEMPLATES.get(q.question_id)
        if template:
            any_followups = True
            lines.append(f"- **[{q.dimension_name}]** {template}")
    if not any_followups:
        lines.append("_No outstanding follow-up questions — every answered dimension scored adequate._")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- 4. Flags — three distinct lists ---
    lines.append("## 🚩 Flags")
    lines.append("")
    lines.append("### 📝 Still need to ask — not yet answered")
    lines.append(
        "> You haven't gotten this from the vendor yet, or aren't sure how to "
        "judge it. This isn't a mark against the vendor — it's your to-do "
        "list. Use the questions above next time you speak with them."
    )
    if result.not_yet_asked:
        for q in result.not_yet_asked:
            lines.append(f"- **[{q.dimension_name}]** {q.script}")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("### 🔴 Vendor wouldn't answer")
    lines.append(
        "> The vendor was asked directly and did not provide this. Treat "
        "this as a signal about their transparency, not just a gap in your "
        "own homework."
    )
    if result.vendor_declined:
        for q in result.vendor_declined:
            lines.append(f"- **[{q.dimension_name}]** {q.script}")
    else:
        lines.append("_None._")
    lines.append("")

    lines.append("### 🟡 Information provided and inadequate")
    if result.inadequate:
        for q in result.inadequate:
            lines.append(f"- **[{q.dimension_name}]** {q.script} _(evidence: {q.evidence})_")
    else:
        lines.append("_None._")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- 5. Narrative ---
    lines.append("## 🧠 What this evaluation actually tells you")
    lines.append("")
    lines.append(narrative if narrative else "_Narrative not generated._")
    lines.append("")
    lines.append("---")
    lines.append("")

    # --- 6. Technical scorecard appendix ---
    lines.append("## 📊 Technical scorecard (appendix)")
    lines.append("")
    for dim in result.dimensions:
        weight_note = f" ×{dim.score_weight}" if dim.score_weight != 1 else ""
        tag = f" — EU AI Act {dim.eu_ai_act_tag}" if dim.eu_ai_act_tag else ""
        lines.append(f"### {dim.number}. {dim.name}{weight_note}{tag}")
        if not dim.any_answered:
            lines.append("_Not answered._")
            lines.append("")
            continue
        line = f"**Raw score:** {dim.raw_score_sum:g}/{dim.max_score_sum:g}"
        if dim.pct is not None:
            line += f" ({dim.pct}%)"
        if dim.score_weight != 1:
            line += (
                f" · **weighted contribution to overall score:** "
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
                f"{q.adjusted_score:g}/{q.max_score:g}{downgrade} |"
            )
        lines.append("")

    lines.append("---")
    lines.append(
        "_CA Project Management Services Ltd (CAPMLTD) · caprojectmgmt.com · "
        "Vendor Claim Stress Test · part of the CA AI Governance Toolkit, "
        "alongside the Model Card Generator and Annotation Brief Builder._"
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# PDF report — mirrors the app's navy-to-green gradient header, traffic-light
# verdict banner, and card-style callout boxes.
# --------------------------------------------------------------------------- #

_NAVY_DARK = (10, 15, 30)
_BRAND_GREEN = (23, 107, 67)
_NAVY = (22, 48, 90)
_RED = (192, 57, 43)
_RED_DARK = (146, 43, 33)
_AMBER = (212, 144, 10)
_AMBER_DARK = (166, 106, 5)
_GREEN = (30, 132, 73)
_GREEN_DARK = (20, 90, 50)
_TEXT_DARK = (26, 26, 26)
_MUTED = (110, 118, 133)
_SCOPE_BG = (255, 247, 230)
_SCOPE_TEXT = (107, 78, 0)
_ASK_BG = (243, 246, 250)
_ASK_TEXT = (51, 71, 91)
_VENDOR_BG = (253, 235, 233)
_VENDOR_TEXT = (110, 33, 25)
_NARRATIVE_BG = (240, 247, 243)

_VERDICT_COLORS = {
    "RED": (_RED, _RED_DARK),
    "AMBER": (_AMBER, _AMBER_DARK),
    "GREEN": (_GREEN, _GREEN_DARK),
}


def _clean(text: str) -> str:
    # fpdf2's core fonts are latin-1 only; sanitize smart punctuation etc.
    replacements = {
        "‘": "'", "’": "'", "“": '"', "”": '"',
        "–": "-", "—": "-", "…": "...",
        "🔴": "[RED]", "🟡": "[AMBER]", "🟢": "[GREEN]",
        "→": "->", "×": "x",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")


def build_pdf_report(result, narrative: str, vendor_name: str = "") -> bytes:
    """Render a branded PDF version of the report using fpdf2."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    def content_width():
        return pdf.w - pdf.l_margin - pdf.r_margin

    def gradient_rect(x, y, w, h, c1, c2, steps=60):
        for i in range(steps):
            t = i / (steps - 1)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            pdf.set_fill_color(r, g, b)
            seg_w = w / steps
            pdf.rect(x + i * seg_w, y, seg_w + 0.6, h, style="F")

    def reset_colors():
        pdf.set_text_color(*_TEXT_DARK)
        pdf.set_fill_color(255, 255, 255)

    def section_header(text):
        pdf.ln(3)
        pdf.set_fill_color(*_NAVY)
        pdf.rect(pdf.l_margin, pdf.get_y(), 2.2, 6.5, style="F")
        pdf.set_xy(pdf.l_margin + 4.5, pdf.get_y())
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*_NAVY)
        pdf.cell(0, 6.5, _clean(text), new_x="LMARGIN", new_y="NEXT")
        reset_colors()
        pdf.ln(1.5)

    def body(text, size=10.5, color=_TEXT_DARK, style=""):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", style, size)
        pdf.set_text_color(*color)
        pdf.multi_cell(0, 5.8, _clean(text), new_x="LMARGIN", new_y="NEXT")
        reset_colors()

    def callout(text, bg, text_color):
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_fill_color(*bg)
        pdf.set_text_color(*text_color)
        pdf.multi_cell(0, 5.4, _clean(text), fill=True, padding=3, new_x="LMARGIN", new_y="NEXT")
        reset_colors()
        pdf.ln(1.5)

    def pill(text, bg):
        pdf.set_font("Helvetica", "B", 8.5)
        w = pdf.get_string_width(text) + 6
        pdf.set_fill_color(*bg)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(w, 5.5, text, fill=True, align="C", new_x="LMARGIN", new_y="NEXT")
        reset_colors()

    def bullet_list(items):
        pdf.set_font("Helvetica", "", 10)
        for item in items:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 5.6, _clean(f"-  {item}"))
        reset_colors()

    # --- Header banner: navy -> green gradient, logo badge, title, tagline ---
    x0, y0 = pdf.l_margin, pdf.get_y()
    w = content_width()
    banner_h = 34
    gradient_rect(x0, y0, w, banner_h, _NAVY_DARK, _BRAND_GREEN)

    pdf.set_fill_color(255, 255, 255)
    pdf.rect(x0 + 5, y0 + 6, 15, 15, style="F", round_corners=True, corner_radius=3)
    pdf.set_xy(x0 + 5, y0 + 6)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*_NAVY_DARK)
    pdf.cell(15, 15, "CA", align="C")

    title = "Vendor Claim Stress Test" + (f" — {vendor_name}" if vendor_name else "")
    pdf.set_xy(x0 + 24, y0 + 6)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(w - 28, 6, _clean(title))

    pdf.set_xy(x0 + 24, y0 + 13)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(
        w - 28, 4.5,
        _clean("Your vendor showed you a great number. This tells you whether you can trust it."),
    )

    pdf.set_xy(x0 + 5, y0 + banner_h - 7)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(230, 235, 232)
    pdf.cell(
        0, 4,
        _clean("EXCELLENCE | HONESTY | QUALITY  ·  CA PROJECT MANAGEMENT SERVICES LTD  ·  CAPROJECTMGMT.COM"),
        new_x="LMARGIN", new_y="NEXT",
    )

    reset_colors()
    pdf.set_xy(pdf.l_margin, y0 + banner_h + 3)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_MUTED)
    pdf.cell(0, 5, _clean(f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    reset_colors()
    pdf.ln(1)

    # --- Scope box ---
    callout(
        "Scope: This tool checks whether the evidence you've been shown is "
        "honest and relevant. It does not assess pricing, contracts, vendor "
        "viability, or whether you've picked the right use case.",
        _SCOPE_BG, _SCOPE_TEXT,
    )

    # --- Verdict banner ---
    c1, c2 = _VERDICT_COLORS.get(result.verdict, (_AMBER, _AMBER_DARK))
    vx, vy = pdf.l_margin, pdf.get_y()
    vw = content_width()
    vh = 22
    gradient_rect(vx, vy, vw, vh, c1, c2)
    pdf.set_xy(vx + 5, vy + 4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5, _clean(f"VERDICT: {result.verdict}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(vx + 5, vy + 10)
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(vw - 10, 7, _clean(result.verdict_line), new_x="LMARGIN", new_y="NEXT")
    reset_colors()
    pdf.set_xy(pdf.l_margin, vy + vh + 3)

    if result.weighted_pct is not None:
        body(f"Weighted evidence score: {result.weighted_pct}%", style="B")
        body(
            f"(wizard {result.completion_pct}% answered — this means every "
            "question has a recorded response, including 'I haven't asked "
            "yet.' It is not a measure of how much evidence you actually "
            "have; see Flags below for outstanding gaps.)",
            size=8.5, color=_MUTED,
        )
    pdf.ln(1)

    # --- Evaluator Independence ---
    section_header("Evaluator Independence")
    body(f"Who ran this evaluation: {GATE_ANSWER_LABELS.get(result.gate_answer, 'Not answered')}", style="B")
    if result.independence_gate_failed is None:
        pill("NOT YET ANSWERED", _AMBER)
    elif result.independence_gate_failed:
        pill("GATE FAILED", _RED)
    else:
        pill("PASSED", _GREEN)
    pdf.ln(1)
    body(
        f"Why it matters: an evaluation run and reported by the model's own "
        f"team has an inherent conflict of interest — it does not tell you "
        f"anything about how the model performs under scrutiny it didn't "
        f"design for itself. (Tagged EU AI Act {GLOBAL_ART9_TAG}.)",
        size=9, color=_MUTED,
    )

    if result.dimension_3_gate_failed:
        pdf.ln(1)
        callout(
            "Gate: blended-only reporting across multiple use cases. This "
            "evaluation covers more than one use case but only a blended "
            "average was provided — the verdict is capped at Amber until a "
            "per-use-case breakdown is supplied.",
            _SCOPE_BG, _SCOPE_TEXT,
        )
    if result.force_red_reasons:
        for reason in result.force_red_reasons:
            callout(f"Forced Red: {reason}", _VENDOR_BG, _VENDOR_TEXT)

    # --- Send these questions to your vendor ---
    section_header("Send these questions to your vendor")
    followup_items = []
    if result.independence_gate_failed is not False:
        followup_items.append(FOLLOWUP_TEMPLATES["gate_independence"])
    for q in result.followup_targets:
        template = FOLLOWUP_TEMPLATES.get(q.question_id)
        if template:
            followup_items.append(f"[{q.dimension_name}] {template}")
    if followup_items:
        bullet_list(followup_items)
    else:
        body("No outstanding follow-up questions — every answered dimension scored adequate.")

    # --- Flags ---
    section_header("Flags")

    body("Still need to ask — not yet answered", style="B")
    callout(
        "You haven't gotten this from the vendor yet, or aren't sure how to "
        "judge it. This isn't a mark against the vendor — it's your to-do "
        "list. Use the questions above next time you speak with them.",
        _ASK_BG, _ASK_TEXT,
    )
    if result.not_yet_asked:
        bullet_list([f"[{q.dimension_name}] {q.script}" for q in result.not_yet_asked])
    else:
        body("None.")
    pdf.ln(1)

    body("Vendor wouldn't answer", style="B")
    callout(
        "The vendor was asked directly and did not provide this. Treat "
        "this as a signal about their transparency, not just a gap in your "
        "own homework.",
        _VENDOR_BG, _VENDOR_TEXT,
    )
    if result.vendor_declined:
        bullet_list([f"[{q.dimension_name}] {q.script}" for q in result.vendor_declined])
    else:
        body("None.")
    pdf.ln(1)

    body("Information provided and inadequate", style="B")
    if result.inadequate:
        bullet_list([f"[{q.dimension_name}] {q.script} (evidence: {q.evidence})" for q in result.inadequate])
    else:
        body("None.")

    # --- Narrative ---
    section_header("What this evaluation actually tells you")
    callout(narrative or "Narrative not generated.", _NARRATIVE_BG, _TEXT_DARK)

    # --- Technical scorecard appendix ---
    section_header("Technical scorecard (appendix)")
    for dim in result.dimensions:
        tag = f" — EU AI Act {dim.eu_ai_act_tag}" if dim.eu_ai_act_tag else ""
        weight_note = f" (x{dim.score_weight})" if dim.score_weight != 1 else ""
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(*_NAVY)
        pdf.multi_cell(0, 6, _clean(f"{dim.number}. {dim.name}{weight_note}{tag}"))
        reset_colors()
        if not dim.any_answered:
            body("Not answered.", size=9.5, color=_MUTED)
            continue
        score_line = f"Raw score: {dim.raw_score_sum:g}/{dim.max_score_sum:g}"
        if dim.pct is not None:
            score_line += f" ({dim.pct}%)"
        if dim.score_weight != 1:
            score_line += (
                f" · weighted contribution: {dim.weighted_score:g}/{dim.weighted_max:g} "
                f"(raw x{dim.score_weight})"
            )
        body(score_line, size=9.5, color=_MUTED)
        for q in dim.questions:
            downgrade = " (downgraded - self-reported)" if q.downgraded else ""
            body(
                f"-  {q.script}\n   {q.score_label} | evidence: {q.evidence} | "
                f"score {q.adjusted_score:g}/{q.max_score:g}{downgrade}",
                size=9.5,
            )
        pdf.ln(1)

    # --- Footer ---
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*_MUTED)
    pdf.multi_cell(
        0, 4.5,
        _clean(
            "CA Project Management Services Ltd (CAPMLTD) - caprojectmgmt.com - "
            "Vendor Claim Stress Test - part of the CA AI Governance Toolkit, "
            "alongside the Model Card Generator and Annotation Brief Builder."
        ),
        align="C",
    )
    reset_colors()

    buf = BytesIO()
    pdf_bytes = pdf.output()
    buf.write(bytes(pdf_bytes))
    buf.seek(0)
    return buf.getvalue()
