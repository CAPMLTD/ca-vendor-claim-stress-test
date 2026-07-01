"""
Vendor Claim Stress Test
CA AI Governance Toolkit — CAPMLTD

A tool that lets a non-technical buyer pressure-test an AI vendor's evaluation
claims before purchase. It does not score whether a model is good — it scores
whether the evaluation evidence the buyer has been shown is honest and
relevant to their stated use case.
"""

import copy

import streamlit as st

from src.data import (
    DIMENSIONS,
    GATE_QUESTION,
    WORKED_EXAMPLE,
    TOTAL_QUESTIONS,
    GLOBAL_ART9_TAG,
)
from src.scoring import compute_result, compute_dimension_result
from src.ui import (
    inject_css,
    render_header,
    render_scope_box,
    render_footer,
    verdict_banner,
    pill,
)
from src.export import build_markdown_report, build_pdf_report
from src.claude_integration import generate_narrative

STAGE_LANDING = "landing"
STAGE_GATE = "gate"
STAGE_RESULTS = "results"
DIMENSION_STAGES = [d["id"] for d in DIMENSIONS]
ALL_STAGES = [STAGE_LANDING, STAGE_GATE] + DIMENSION_STAGES + [STAGE_RESULTS]


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #

def init_state():
    if "stage" not in st.session_state:
        st.session_state.stage = STAGE_LANDING
    if "answers" not in st.session_state:
        st.session_state.answers = {d["id"]: {} for d in DIMENSIONS}
    if "gate_answer" not in st.session_state:
        st.session_state.gate_answer = None
    if "multi_use_case" not in st.session_state:
        st.session_state.multi_use_case = None
    if "vendor_name" not in st.session_state:
        st.session_state.vendor_name = ""
    if "narrative" not in st.session_state:
        st.session_state.narrative = None
    if "narrative_error" not in st.session_state:
        st.session_state.narrative_error = None


def go_to(stage: str):
    st.session_state.stage = stage


def load_worked_example():
    st.session_state.answers = copy.deepcopy(WORKED_EXAMPLE["answers"])
    st.session_state.gate_answer = WORKED_EXAMPLE["gate_answer"]
    st.session_state.multi_use_case = WORKED_EXAMPLE["multi_use_case"]
    st.session_state.vendor_name = "Worked example (anonymised retail bake-off)"
    st.session_state.narrative = None
    st.session_state.narrative_error = None
    st.session_state.stage = STAGE_RESULTS


def reset_all():
    st.session_state.stage = STAGE_LANDING
    st.session_state.answers = {d["id"]: {} for d in DIMENSIONS}
    st.session_state.gate_answer = None
    st.session_state.multi_use_case = None
    st.session_state.vendor_name = ""
    st.session_state.narrative = None
    st.session_state.narrative_error = None


# --------------------------------------------------------------------------- #
# Progress helpers
# --------------------------------------------------------------------------- #

def progress_snapshot():
    answered_questions = 0
    answered_dimensions = 0
    for dimension in DIMENSIONS:
        dr = compute_dimension_result(dimension, st.session_state.answers.get(dimension["id"], {}))
        answered_questions += len(dr.questions)
        if dr.all_answered:
            answered_dimensions += 1
    # +1 for the Evaluator Independence gate question, so the wizard can
    # never claim "100%" while that mandatory question is still unanswered.
    if st.session_state.gate_answer is not None:
        answered_questions += 1
    completion_pct = round(100 * answered_questions / (TOTAL_QUESTIONS + 1), 1)
    return answered_dimensions, len(DIMENSIONS), completion_pct


def render_sidebar():
    with st.sidebar:
        st.markdown("### Progress")
        answered_dims, total_dims, completion_pct = progress_snapshot()
        st.progress(min(completion_pct / 100, 1.0))
        st.caption(f"{answered_dims} of {total_dims} dimensions fully answered")
        st.caption(f"{completion_pct}% of questions answered in the wizard")

        gate_done = st.session_state.gate_answer is not None
        st.caption(f"Evaluator independence: {'answered' if gate_done else 'not answered'}")

        if completion_pct >= 40:
            st.success("You've answered enough to see a directional result.")

        st.markdown("---")
        st.markdown("**Jump to:**")
        if st.button("Landing", use_container_width=True):
            go_to(STAGE_LANDING)
            st.rerun()
        if st.button("Evaluator independence", use_container_width=True):
            go_to(STAGE_GATE)
            st.rerun()
        for dimension in DIMENSIONS:
            label = f"{dimension['number']}. {dimension['name']}"
            if st.button(label, use_container_width=True, key=f"nav_{dimension['id']}"):
                go_to(dimension["id"])
                st.rerun()
        can_see_results = completion_pct >= 40
        if st.button(
            "See results",
            type="primary",
            use_container_width=True,
            disabled=not can_see_results,
        ):
            go_to(STAGE_RESULTS)
            st.rerun()
        if not can_see_results:
            st.caption("Answer at least a few questions to unlock results.")

        st.markdown("---")
        if st.button("Start over", use_container_width=True):
            reset_all()
            st.rerun()


# --------------------------------------------------------------------------- #
# Screens
# --------------------------------------------------------------------------- #

def render_landing():
    render_header()
    render_scope_box()

    st.markdown(
        "Before you buy, your vendor showed you an evaluation with a great "
        "number on it. This tool doesn't tell you whether the model is good — "
        "it tells you whether you can trust the evidence you were shown."
    )
    st.markdown(
        "What follows is a series of questions you should get clear answers to "
        "— directly from the vendor, or from your own read of the evidence they "
        "gave you — before you sign off on procuring their solution. Answer "
        "honestly based on what you've actually been told; if you're not sure, "
        "say so, and the tool will tell you exactly what to go find out before "
        "you proceed."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("See how this works (worked example)", type="secondary", use_container_width=True):
            load_worked_example()
            st.rerun()
    with col2:
        if st.button("Start my own stress test", type="primary", use_container_width=True):
            go_to(STAGE_GATE)
            st.rerun()

    st.markdown("---")
    st.markdown(
        "**How it works:** you'll be asked one gate question about who ran the "
        "evaluation, then walked through seven dimensions of evaluation "
        "evidence, one question at a time. You can stop and view a directional "
        "result once you've answered around 40% of the questions."
    )

    render_footer()


def render_gate():
    render_header("Ask this before anything else.")
    render_scope_box()

    st.subheader(GATE_QUESTION["title"])
    st.markdown(f"_{GATE_QUESTION['script']}_")

    option_labels = [label for _, label in GATE_QUESTION["options"]]
    option_keys = [key for key, _ in GATE_QUESTION["options"]]
    current_index = (
        option_keys.index(st.session_state.gate_answer)
        if st.session_state.gate_answer in option_keys
        else None
    )
    choice = st.radio(
        "Answer",
        options=option_labels,
        index=current_index,
        label_visibility="collapsed",
        key="gate_radio",
    )
    if choice is not None:
        st.session_state.gate_answer = option_keys[option_labels.index(choice)]

    st.caption(
        "Why this comes first: an evaluation run and reported by the model's "
        "own team has a built-in conflict of interest — this alone can cap "
        "how much you should trust everything that follows, tagged EU AI Act "
        f"{GLOBAL_ART9_TAG}."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Back", use_container_width=True):
            go_to(STAGE_LANDING)
            st.rerun()
    with col2:
        if st.button("Continue to Dimension 1", type="primary", use_container_width=True):
            go_to(DIMENSIONS[0]["id"])
            st.rerun()

    render_footer()


def render_dimension(dimension: dict):
    render_header()
    render_scope_box()

    idx = DIMENSION_STAGES.index(dimension["id"])
    st.markdown(f"#### Dimension {dimension['number']} of 7")
    st.subheader(dimension["name"])
    if dimension.get("eu_ai_act_tag"):
        st.markdown(pill(f"EU AI Act {dimension['eu_ai_act_tag']}", "grey"), unsafe_allow_html=True)
    if dimension.get("gate_dimension"):
        st.markdown(
            pill("Gate dimension — caps verdict at Amber if failed", "amber"),
            unsafe_allow_html=True,
        )
    if dimension.get("score_weight", 1) > 1:
        st.markdown(
            pill(f"Double-weighted in scoring (×{dimension['score_weight']})", "red"),
            unsafe_allow_html=True,
        )

    # Reserve the spot for the progress indicator now, fill it in after this
    # run's widget interactions have updated session_state below — otherwise
    # it would display last run's (stale) numbers.
    progress_placeholder = st.empty()

    st.markdown("---")

    if dimension["id"] == "d3_percase":
        st.markdown("**First — does this evaluation cover multiple use cases?**")
        muc_options = ["Yes — multiple use cases", "No — single use case"]
        muc_index = None
        if st.session_state.multi_use_case is True:
            muc_index = 0
        elif st.session_state.multi_use_case is False:
            muc_index = 1
        muc_choice = st.radio(
            "Multiple use cases?", muc_options, index=muc_index, label_visibility="collapsed",
            key="d3_multi_use_case",
        )
        if muc_choice is not None:
            st.session_state.multi_use_case = muc_choice == muc_options[0]
        st.markdown("---")

    dim_answers = st.session_state.answers[dimension["id"]]

    for question in dimension["questions"]:
        with st.container(border=True):
            minor = question.get("minor_weight", 1.0) < 1.0
            script = question["script"]
            st.markdown(f'<div class="ca-question-script">{script}</div>', unsafe_allow_html=True)
            if minor:
                st.caption("Minor weight in scoring.")

            example_good = question.get("example_good")
            example_bad = question.get("example_bad")
            if example_good and example_bad:
                st.markdown(
                    f'<div class="ca-question-example">'
                    f"<b>Strong answer looks like:</b> {example_good}<br/>"
                    f"<b>Weak answer looks like:</b> {example_bad}"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            combined_options = question["combined_options"]
            option_labels = [label for label, _, _ in combined_options]
            option_by_pair = {
                (score_key, evidence): label for label, score_key, evidence in combined_options
            }
            option_by_label = {
                label: (score_key, evidence) for label, score_key, evidence in combined_options
            }

            existing = dim_answers.get(question["id"])
            existing_index = None
            if existing:
                existing_label = option_by_pair.get(
                    (existing["score_key"], existing["evidence"])
                )
                if existing_label in option_labels:
                    existing_index = option_labels.index(existing_label)

            choice = st.radio(
                "Answer",
                options=option_labels,
                index=existing_index,
                key=f"combined_{question['id']}",
                label_visibility="collapsed",
            )

            if choice is not None:
                score_key, evidence = option_by_label[choice]
                dim_answers[question["id"]] = {"score_key": score_key, "evidence": evidence}
            elif question["id"] in dim_answers:
                del dim_answers[question["id"]]

    answered_dims, total_dims, completion_pct = progress_snapshot()
    with progress_placeholder.container():
        st.progress(min(completion_pct / 100, 1.0))
        st.caption(f"{answered_dims} of {total_dims} dimensions answered · {completion_pct}% of questions answered in the wizard")
        if completion_pct >= 40:
            st.markdown(
                '<div class="ca-directional-msg">You\'ve answered enough to see a '
                "directional result — jump to \"See results\" in the sidebar any "
                "time.</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        prev_stage = STAGE_GATE if idx == 0 else DIMENSION_STAGES[idx - 1]
        if st.button("Back", use_container_width=True):
            go_to(prev_stage)
            st.rerun()
    with col2:
        if idx < len(DIMENSION_STAGES) - 1:
            if st.button("Next dimension", type="primary", use_container_width=True):
                go_to(DIMENSION_STAGES[idx + 1])
                st.rerun()
        else:
            if st.button("See results", type="primary", use_container_width=True):
                go_to(STAGE_RESULTS)
                st.rerun()
    with col3:
        _, _, cp = progress_snapshot()
        if cp >= 40:
            if st.button("Skip to results", use_container_width=True):
                go_to(STAGE_RESULTS)
                st.rerun()

    render_footer()


def render_results():
    render_header()
    render_scope_box()

    result = compute_result(
        st.session_state.answers,
        st.session_state.gate_answer,
        st.session_state.multi_use_case,
    )

    if result.completion_pct < 100:
        st.info(
            f"Directional result — {result.completion_pct}% of questions answered "
            "in the wizard so far. Answer more dimensions for a fully confirmed "
            "verdict."
        )
    else:
        st.caption(
            "All questions have a recorded answer in the wizard — including any "
            "marked \"I'm not sure / haven't asked yet.\" That's wizard "
            "completion, not evidence completeness: check \"Still need to ask\" "
            "below for what's still outstanding."
        )

    # 1. Verdict banner
    verdict_banner(result.verdict, result.verdict_line)

    # 2. Evaluator independence — separate and prominent
    st.markdown("### Evaluator Independence")
    answer_map = {
        "same_team": "Same team",
        "internal_separate": "Internal-separate team",
        "independent_third_party": "Independent third party",
        "dont_know": "Don't know",
    }
    gate_label = answer_map.get(result.gate_answer, "Not answered")
    if result.independence_gate_failed is None:
        fail_pill = pill("NOT YET ANSWERED", "amber")
    elif result.independence_gate_failed:
        fail_pill = pill("GATE FAILED", "red")
    else:
        fail_pill = pill("PASSED", "green")
    st.markdown(
        f"**Who ran this evaluation:** {gate_label} &nbsp; {fail_pill}",
        unsafe_allow_html=True,
    )
    st.caption(
        "Why it matters: an evaluation run and reported by the model's own team "
        "has a built-in conflict of interest. This is checked separately from "
        f"the 7-dimension score because it can undermine every other answer "
        f"(EU AI Act {GLOBAL_ART9_TAG})."
    )

    if result.dimension_3_gate_failed:
        st.warning(
            "**Gate: blended-only reporting across multiple use cases.** This "
            "evaluation covers more than one use case but only a blended "
            "average was provided — the verdict is capped at Amber until a "
            "per-use-case breakdown is supplied."
        )
    if result.force_red_reasons:
        for reason in result.force_red_reasons:
            st.error(reason)

    st.markdown("---")

    # 3. Send these questions to your vendor
    st.markdown("### Send these questions to your vendor")
    from src.data import FOLLOWUP_TEMPLATES

    any_followups = False
    if result.independence_gate_failed is not False:
        any_followups = True
        st.markdown(f"- {FOLLOWUP_TEMPLATES['gate_independence']}")
    for q in result.followup_targets:
        template = FOLLOWUP_TEMPLATES.get(q.question_id)
        if template:
            any_followups = True
            st.markdown(f"- **[{q.dimension_name}]** {template}")
    if not any_followups:
        st.markdown("No outstanding follow-up questions — every answered dimension scored adequate.")
    else:
        followup_text = "\n".join(
            (["- " + FOLLOWUP_TEMPLATES["gate_independence"]] if result.independence_gate_failed is not False else [])
            + [
                f"- [{q.dimension_name}] {FOLLOWUP_TEMPLATES.get(q.question_id, '')}"
                for q in result.followup_targets
                if q.question_id in FOLLOWUP_TEMPLATES
            ]
        )
        st.text_area("Copy-pasteable list", value=followup_text, height=160, label_visibility="collapsed")

    st.markdown("---")

    # 4. Flag lists — clearly separated into three distinct categories
    st.markdown("### Flags")

    st.markdown("**Still need to ask — not yet answered**")
    st.caption(
        "You haven't gotten this from the vendor yet, or aren't sure how to judge "
        "it. This isn't a mark against the vendor — it's your to-do list. Use the "
        "questions above next time you speak with them."
    )
    if result.not_yet_asked:
        for q in result.not_yet_asked:
            st.markdown(f"- [{q.dimension_name}] {q.script}")
    else:
        st.markdown("_None._")

    st.markdown("**Vendor wouldn't answer**")
    st.caption(
        "The vendor was asked directly and did not provide this. Treat this as a "
        "signal about their transparency, not just a gap in your own homework."
    )
    if result.vendor_declined:
        for q in result.vendor_declined:
            st.markdown(f"- [{q.dimension_name}] {q.script}")
    else:
        st.markdown("_None._")

    st.markdown("**Information provided and inadequate**")
    if result.inadequate:
        for q in result.inadequate:
            st.markdown(f"- [{q.dimension_name}] {q.script} _(evidence: {q.evidence})_")
    else:
        st.markdown("_None._")

    st.markdown("---")

    # 5. Claude narrative
    st.markdown("### What this evaluation actually tells you")
    context_note = WORKED_EXAMPLE["narrative_context"] if st.session_state.vendor_name.startswith("Worked example") else ""

    # Generate automatically the first time results are viewed — this is the
    # single most valuable output for the buyer, so it shouldn't depend on
    # remembering to click a button before exporting. Cached in session_state
    # so it only fires once per result set, not on every widget interaction.
    if st.session_state.narrative is None and st.session_state.narrative_error is None:
        with st.spinner("Asking Claude to ground a narrative in your answers..."):
            try:
                st.session_state.narrative = generate_narrative(result, context_note)
            except Exception as exc:  # noqa: BLE001 — surfaced to the user
                st.session_state.narrative_error = str(exc)

    if st.session_state.narrative:
        st.markdown(st.session_state.narrative)
        if st.button("Regenerate"):
            st.session_state.narrative = None
            st.session_state.narrative_error = None
            st.rerun()
    elif st.session_state.narrative_error:
        st.warning(st.session_state.narrative_error)
        if st.button("Try again"):
            st.session_state.narrative_error = None
            st.rerun()

    st.markdown("---")

    # 6. Technical scorecard appendix (collapsed by default)
    with st.expander("Technical scorecard (full 7-dimension breakdown)"):
        for dim in result.dimensions:
            weight_note = f" ×{dim.score_weight}" if dim.score_weight != 1 else ""
            tag = f" — EU AI Act {dim.eu_ai_act_tag}" if dim.eu_ai_act_tag else ""
            st.markdown(f"**{dim.number}. {dim.name}{weight_note}{tag}**")
            if not dim.any_answered:
                st.caption("Not answered.")
                continue
            pct_str = f" ({dim.pct}%)" if dim.pct is not None else ""
            weighted_note = ""
            if dim.score_weight != 1:
                weighted_note = (
                    f" · weighted contribution: {dim.weighted_score:g}/{dim.weighted_max:g} "
                    f"(raw ×{dim.score_weight})"
                )
            st.caption(f"Raw score: {dim.raw_score_sum:g}/{dim.max_score_sum:g}{pct_str}{weighted_note}")
            for q in dim.questions:
                downgrade = " _(downgraded — self-reported)_" if q.downgraded else ""
                st.markdown(
                    f"- {q.script}<br/>&nbsp;&nbsp;→ **{q.score_label}** · "
                    f"evidence: {q.evidence} · score {q.adjusted_score}/{q.max_score}"
                    f"{downgrade}",
                    unsafe_allow_html=True,
                )
            st.markdown("")

    st.markdown("---")

    # Export
    st.markdown("### Export report")
    vendor_name = st.text_input("Vendor / product name (for the report title)", value=st.session_state.vendor_name)
    st.session_state.vendor_name = vendor_name

    if st.session_state.narrative:
        narrative_for_export = st.session_state.narrative
    elif st.session_state.narrative_error:
        narrative_for_export = f"Narrative unavailable: {st.session_state.narrative_error}"
    else:
        narrative_for_export = ""
    md_report = build_markdown_report(result, narrative_for_export, vendor_name)

    col_md, col_pdf = st.columns(2)
    with col_md:
        st.download_button(
            "Download Markdown report",
            data=md_report,
            file_name="vendor_claim_stress_test.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_pdf:
        try:
            pdf_bytes = build_pdf_report(result, narrative_for_export, vendor_name)
            st.download_button(
                "Download PDF report",
                data=pdf_bytes,
                file_name="vendor_claim_stress_test.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:  # noqa: BLE001
            st.caption(f"PDF export unavailable: {exc}")

    render_footer()


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def main():
    st.set_page_config(
        page_title="Vendor Claim Stress Test — CAPMLTD",
        page_icon="🚦",
        layout="centered",
    )
    inject_css()
    init_state()

    stage = st.session_state.stage

    # Render the page content first so this run's widget interactions update
    # session_state.answers before the sidebar reads it — st.sidebar calls
    # still land in the sidebar regardless of call order, so this only fixes
    # the "progress lags one click behind" staleness, not the visual layout.
    if stage == STAGE_LANDING:
        render_landing()
    elif stage == STAGE_GATE:
        render_gate()
    elif stage in DIMENSION_STAGES:
        dimension = next(d for d in DIMENSIONS if d["id"] == stage)
        render_dimension(dimension)
    elif stage == STAGE_RESULTS:
        render_results()
    else:
        st.session_state.stage = STAGE_LANDING
        st.rerun()
        return

    if stage != STAGE_LANDING:
        render_sidebar()


if __name__ == "__main__":
    main()
