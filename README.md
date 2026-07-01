# Vendor Claim Stress Test

Part of the **CA AI Governance Toolkit** (CAPMLTD), alongside the Model Card
Generator and the Annotation Brief Builder.

> Your vendor showed you a great number. This tool tells you whether you can
> trust it.

## What this tool does — and doesn't do

The Vendor Claim Stress Test does not score whether an AI model is good. It
scores whether the evaluation evidence a buyer has been shown is **honest and
relevant** to their stated use case. It does not assess pricing, contracts,
vendor viability, or whether the buyer picked the right use case.

A non-technical buyer answers a short wizard of vendor-facing questions (each
phrased as a script they can read straight to the vendor), and the tool:

1. Checks whether the evaluation was run by an independent party (the
   "global gate" question).
2. Scores seven dimensions of evaluation evidence — test set provenance,
   distributional validity, per-use-case breakdown, temporal
   representativeness, metric/baseline/threshold integrity, leakage risk
   (double-weighted), and reporting transparency.
3. Applies self-reported downgrades, dimension weighting, and gate logic to
   produce a RED / AMBER / GREEN verdict.
4. Generates a list of follow-up questions to send back to the vendor.
5. Calls Claude (`claude-sonnet-4-5`) to write a short, evidence-grounded
   narrative explaining what the evaluation actually tells the buyer versus
   what it's being presented as telling them.
6. Exports a Markdown or PDF report for the buyer to forward internally.

## Running locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
streamlit run app.py
```

Or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and
fill in your key.

## Deploying to Streamlit Community Cloud

1. Push this repository to `capmltd/ca-vendor-claim-stress-test`.
2. Create a new app on [Streamlit Community Cloud](https://share.streamlit.io)
   pointing at `app.py` on the main branch.
3. Under **Settings → Secrets**, add:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```

## Project structure

```
app.py                     Streamlit wizard UI and screen flow
src/data.py                Dimensions, questions, scale, follow-up templates, worked example
src/scoring.py              Scoring engine: downgrades, weighting, gates, verdict
src/claude_integration.py   Claude API call for the grounded narrative
src/export.py               Markdown / PDF report generation
src/ui.py                   Shared CAPMLTD branding, traffic-light styling
```

## Scoring logic summary

- Each of the 16 questions across 7 dimensions is answered on a 3-state
  scale: **Provided & adequate** (2), **Provided & inadequate** (1),
  **Not provided / don't know** (0) — plus an evidence tag (self-reported,
  documented & verifiable, or not applicable).
- Self-reported answers on **Distributional Validity** or **Leakage Risk**
  are downgraded one tier before weighting.
- **Leakage Risk** and **Distributional Validity** are double-weighted; all
  other dimensions are weighted ×1.
- **Gates** (independent of the percentage score):
  - Evaluator independence gate failed (same team / don't know) → caps
    verdict at Amber.
  - Multi-use-case evaluation reported as a blended average only → caps
    verdict at Amber.
  - Distributional Validity or Leakage Risk scoring zero → forces Red.
- **Verdict bands**: RED if any force-red condition or weighted score
  &lt; 60%; AMBER if a gate cap applies or weighted score is 60–84%; GREEN
  only at ≥85% with no gate failures.
