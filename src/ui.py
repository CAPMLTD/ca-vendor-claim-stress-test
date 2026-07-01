"""Shared visual style: CAPMLTD branding, traffic-light treatment, header/footer."""

import streamlit as st

BRAND_CSS = """
<style>
:root {
    --ca-navy: #0B1F3A;
    --ca-navy-dark: #0A0F1E;
    --ca-navy-light: #16305A;
    --ca-brand-green: #176B43;
    --ca-red: #C0392B;
    --ca-amber: #D4900A;
    --ca-green: #1E8449;
    --ca-bg: #F7F8FA;
}

/* Streamlit's fixed top toolbar (hamburger / Deploy / GitHub icons on Community
   Cloud) sits above the block container. Without enough top padding it overlaps
   the rounded top corners of our custom header, making it look clipped. */
.block-container {
    padding-top: 3rem;
    max-width: 900px;
}

.ca-header {
    background: linear-gradient(135deg, var(--ca-navy-dark) 0%, var(--ca-brand-green) 100%);
    color: white;
    padding: 1.3rem 1.6rem;
    border-radius: 14px;
    margin-bottom: 1.2rem;
}
.ca-header-top {
    display: flex;
    align-items: center;
    gap: 0.9rem;
}
.ca-logo-badge {
    flex-shrink: 0;
    width: 46px;
    height: 46px;
    background: white;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 0.95rem;
    color: var(--ca-navy-dark);
    letter-spacing: -0.02em;
}
.ca-header .ca-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin: 0;
}
.ca-header .ca-pitch {
    font-size: 1.0rem;
    opacity: 0.92;
    margin-top: 0.5rem;
}
.ca-header .ca-tagline {
    font-size: 0.72rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-top: 0.9rem;
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

.ca-question-example {
    background: #F3F6FA;
    border-left: 3px solid #8AA4C8;
    border-radius: 4px;
    padding: 0.55rem 0.8rem;
    font-size: 0.85rem;
    color: #33475B;
    margin-bottom: 0.7rem;
}
.ca-question-example b {
    color: #16305A;
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
            <div class="ca-header-top">
                <div class="ca-logo-badge">CA</div>
                <div class="ca-title">&#128678; Vendor Claim Stress Test</div>
            </div>
            <div class="ca-pitch">{subtitle or pitch}</div>
            <div class="ca-tagline">
                EXCELLENCE | HONESTY | QUALITY &middot;
                CA PROJECT MANAGEMENT SERVICES LTD &middot; CAPROJECTMGMT.COM
            </div>
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
            CA Project Management Services Ltd (CAPMLTD) &middot; caprojectmgmt.com
            &middot; Vendor Claim Stress Test &middot; part of the CA AI Governance
            Toolkit, alongside the Model Card Generator and Annotation Brief Builder
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
