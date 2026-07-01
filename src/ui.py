"""Shared visual style: CAPMLTD branding, traffic-light treatment, header/footer."""

import streamlit as st

BRAND_CSS = """
<style>
:root {
    --ca-navy: #0B1F3A;
    --ca-navy-light: #16305A;
    --ca-red: #C0392B;
    --ca-amber: #D4900A;
    --ca-green: #1E8449;
    --ca-bg: #F7F8FA;
}

.block-container {
    padding-top: 1.5rem;
    max-width: 900px;
}

.ca-header {
    background: linear-gradient(90deg, var(--ca-navy) 0%, var(--ca-navy-light) 100%);
    color: white;
    padding: 1.1rem 1.6rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
}
.ca-header .ca-brand {
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.75;
    margin-bottom: 0.15rem;
}
.ca-header .ca-title {
    font-size: 1.65rem;
    font-weight: 700;
    margin: 0;
}
.ca-header .ca-pitch {
    font-size: 1.0rem;
    opacity: 0.92;
    margin-top: 0.35rem;
}

.ca-scope-box {
    background: #FFF7E6;
    border: 1px solid #E8C170;
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    font-size: 0.92rem;
    color: #6B4E00;
    margin-bottom: 1.2rem;
}

.ca-footer {
    text-align: center;
    color: #8A94A6;
    font-size: 0.8rem;
    margin-top: 2.5rem;
    padding-top: 1rem;
    border-top: 1px solid #E3E6EC;
}

.ca-verdict-banner {
    border-radius: 12px;
    padding: 1.4rem 1.6rem;
    color: white;
    margin-bottom: 1.2rem;
}
.ca-verdict-banner.red { background: linear-gradient(90deg, #C0392B, #922B21); }
.ca-verdict-banner.amber { background: linear-gradient(90deg, #D4900A, #A66A05); }
.ca-verdict-banner.green { background: linear-gradient(90deg, #1E8449, #145A32); }
.ca-verdict-banner .ca-verdict-label {
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.85;
}
.ca-verdict-banner .ca-verdict-line {
    font-size: 1.6rem;
    font-weight: 700;
    margin-top: 0.2rem;
}

.ca-pill {
    display: inline-block;
    padding: 0.15rem 0.65rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: white;
}
.ca-pill.red { background: var(--ca-red); }
.ca-pill.amber { background: var(--ca-amber); }
.ca-pill.green { background: var(--ca-green); }
.ca-pill.grey { background: #8A94A6; }

.ca-card {
    background: white;
    border: 1px solid #E3E6EC;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 1rem;
}

.ca-question-script {
    font-size: 1.05rem;
    font-weight: 600;
    color: #16305A;
    margin-bottom: 0.4rem;
}

.ca-directional-msg {
    background: #E9F3EC;
    border: 1px solid #A9D6B7;
    color: #145A32;
    border-radius: 8px;
    padding: 0.6rem 0.9rem;
    font-size: 0.88rem;
    margin: 0.6rem 0 1rem 0;
}
</style>
"""


def inject_css():
    st.markdown(BRAND_CSS, unsafe_allow_html=True)


def render_header(subtitle: str = None):
    pitch = (
        "Your vendor showed you a great number. This tells you whether you can "
        "trust it."
    )
    st.markdown(
        f"""
        <div class="ca-header">
            <div class="ca-brand">CAPMLTD &middot; CA AI Governance Toolkit</div>
            <div class="ca-title">Vendor Claim Stress Test</div>
            <div class="ca-pitch">{subtitle or pitch}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scope_box():
    st.markdown(
        """
        <div class="ca-scope-box">
            <strong>Scope:</strong> This tool checks whether the evidence you've been
            shown is honest and relevant. It does not assess pricing, contracts,
            vendor viability, or whether you've picked the right use case.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer():
    st.markdown(
        """
        <div class="ca-footer">
            CAPMLTD &middot; CA AI Governance Toolkit &middot;
            Vendor Claim Stress Test &middot; part of a suite with the
            Model Card Generator and Annotation Brief Builder
        </div>
        """,
        unsafe_allow_html=True,
    )


def verdict_banner(verdict: str, verdict_line: str):
    css_class = {"RED": "red", "AMBER": "amber", "GREEN": "green"}.get(verdict, "amber")
    st.markdown(
        f"""
        <div class="ca-verdict-banner {css_class}">
            <div class="ca-verdict-label">Verdict: {verdict}</div>
            <div class="ca-verdict-line">{verdict_line}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(text: str, color: str) -> str:
    return f'<span class="ca-pill {color}">{text}</span>'
