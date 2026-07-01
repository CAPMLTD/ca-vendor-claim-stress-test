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

# The two "withheld" sub-flavors carry different follow-up guidance: one is a
# signal about the vendor's transparency, the other is purely the buyer's own
# to-do. Both still score 0 — this only changes how the result screen and
# report explain the gap.
VENDOR_DECLINED_EVIDENCE = "Vendor wouldn't say"
NOT_YET_ASKED_EVIDENCE = "Not yet asked by buyer"

EVIDENCE_TAGS = [
    "Self-reported by vendor",
    "Documented & verifiable",
    VENDOR_DECLINED_EVIDENCE,
    NOT_YET_ASKED_EVIDENCE,
]

# --- Combined answer options -------------------------------------------------
# The buyer picks one plain-language option per question instead of setting
# the score and evidence tag separately. Each question defines its own 6
# tailored option labels (via _opts below) so the wording reads as a direct
# answer to that specific question, rather than a generic template repeated
# 16 times. Every question's 6 options map 1:1 onto the same (score_key,
# evidence) pairs in the same order, so the scoring engine's data model is
# completely unaffected — only the label text changes per question.
#
# The 5th and 6th options both score as "withheld" (0) but are tagged
# differently: the 5th is "I asked and the vendor wouldn't say" (a
# transparency red flag), the 6th is "I haven't asked / I'm not sure" (an
# action item for the buyer, not a mark against the vendor).

_SCORE_EVIDENCE_ORDER = [
    ("adequate", "Documented & verifiable"),
    ("adequate", "Self-reported by vendor"),
    ("inadequate", "Documented & verifiable"),
    ("inadequate", "Self-reported by vendor"),
    ("withheld", VENDOR_DECLINED_EVIDENCE),
    ("withheld", NOT_YET_ASKED_EVIDENCE),
]


def _opts(*labels):
    """Pair 6 tailored labels with the canonical (score_key, evidence) order."""
    assert len(labels) == 6, "each question needs exactly 6 combined-option labels"
    return [
        (label, score_key, evidence)
        for label, (score_key, evidence) in zip(labels, _SCORE_EVIDENCE_ORDER)
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
# Each question: id, script (read-to-vendor phrasing), minor_weight (0.5 or 1.0),
# example_good/example_bad (concrete illustration), combined_options (6 tailored
# labels built via _opts()).
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
                "script": "Was your test data set aside before training started, or put together afterwards?",
                "minor_weight": 1.0,
                "example_good": "They show a dated data-split manifest or contract clause proving the test set was frozen before training began.",
                "example_bad": "They say “yes, obviously” but can't show when or how the split was actually made.",
                "combined_options": _opts(
                    "Yes — they showed a dated record proving the test set was frozen before training",
                    "Yes — they said it was set aside first, but gave no documentation",
                    "They gave documentation, but it doesn't clearly show the test set was frozen before training",
                    "They said something about the timing, but it was just their word, not a clear answer",
                    "No — they wouldn't say when the test set was created",
                    "I'm not sure — I haven't asked them when the test set was created",
                ),
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
                "script": "Was your 'unseen' test data actually from different conditions, or just a different slice of the same environment?",
                "minor_weight": 1.0,
                "example_good": "They specify exactly what differs — a different city, quarter, or hardware batch — and can show it wasn't part of training.",
                "example_bad": "They say it's “unseen” but it's just a random holdout from the same store, same week, same everything else.",
                "combined_options": _opts(
                    "Yes — they documented exactly what's different about the unseen data",
                    "Yes — they said it's genuinely different, but gave no documentation",
                    "They gave documentation, but the 'unseen' data looks like the same environment, just a different slice",
                    "They said it's different, but couldn't explain how — sounds like the same environment",
                    "No — they wouldn't explain what's actually different about the unseen data",
                    "I'm not sure — I haven't asked them what's different about the unseen data",
                ),
            },
            {
                "id": "d2_q2",
                "script": "Did they break results down by site/subgroup/condition, or just give you one overall number?",
                "minor_weight": 1.0,
                "example_good": "They hand over a results table broken down by site, subgroup, or condition, not just one topline number.",
                "example_bad": "They give you one blended accuracy figure and no way to see if it holds up everywhere.",
                "combined_options": _opts(
                    "Yes — they gave a documented breakdown by site, subgroup, or condition",
                    "Yes — they said results hold up across sites/subgroups, but only gave one topline number",
                    "They gave documentation, but it's still mostly one blended number, not a real breakdown",
                    "They mentioned a breakdown exists, but only ever showed one overall number",
                    "No — they only gave one overall number, no breakdown at all",
                    "I'm not sure — I haven't asked for a breakdown by site or subgroup",
                ),
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
                "script": "If this covers multiple use cases, do they report performance per use case, or just a blended average?",
                "minor_weight": 1.0,
                "example_good": "They provide a separate performance number for each use case you'll actually deploy.",
                "example_bad": "They give you one blended number across every use case, with no per-case breakdown.",
                "combined_options": _opts(
                    "Yes — they gave a documented breakdown of performance per use case",
                    "Yes — they said performance is broken out per use case, but gave no documentation",
                    "They gave documentation, but it's still a blended average, not broken out per use case",
                    "They said something about per-use-case performance, but only ever showed a blended number",
                    "No — they report the blended average, with no visibility of performance by use case",
                    "I'm not sure — I haven't asked whether they report performance per use case",
                ),
            },
            {
                "id": "d3_q2",
                "script": (
                    "Is a false positive or a false negative more costly to your business — "
                    "and does their evaluation reflect that, or is it one blended number that hides "
                    "which one you're actually exposed to?"
                ),
                "minor_weight": 1.0,
                "example_good": "They ask which error type costs you more, then show precision/recall (or similar) split accordingly.",
                "example_bad": "They only give one blended accuracy number that doesn't say which type of mistake you're exposed to.",
                "combined_options": _opts(
                    "Yes — they asked which error type costs us more and documented the split accordingly",
                    "Yes — they said they accounted for the cost difference, but didn't document the split",
                    "They gave documentation, but it doesn't show which error type we're actually exposed to",
                    "They said something about error costs, but only ever gave one blended number",
                    "No — it's one blended number, with no visibility into which error type we're exposed to",
                    "I'm not sure — I haven't asked which error type this evaluation reflects",
                ),
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
                "script": "Was the test data collected under conditions like what you'll actually deploy into, or is it stale/unrepresentative?",
                "minor_weight": 1.0,
                "example_good": "The test data comes from conditions matching your deployment — same season, region, customer mix, etc.",
                "example_bad": "The test data is old, from a different market, or otherwise doesn't resemble what you'll deploy into.",
                "combined_options": _opts(
                    "Yes — they documented that test conditions match our deployment environment",
                    "Yes — they said the conditions match our deployment, but gave no documentation",
                    "They gave documentation, but the conditions don't clearly match our deployment environment",
                    "They said something about the conditions, but it sounds stale or unrepresentative",
                    "No — they wouldn't confirm whether the test conditions match our deployment",
                    "I'm not sure — I haven't asked whether the test conditions match our deployment",
                ),
            },
            {
                "id": "d4_q2",
                "script": "Are these static test cases, or do they reflect real-world conditions changing over time?",
                "minor_weight": 1.0,
                "example_good": "They explain how they monitor and re-test as real-world conditions shift, with a plan for ongoing checks.",
                "example_bad": "It's a one-off test from a single point in time, with no plan to check whether it still holds.",
                "combined_options": _opts(
                    "Yes — they documented a plan for ongoing re-testing as conditions change",
                    "Yes — they said they monitor for drift over time, but didn't document a specific plan",
                    "They gave documentation, but it's still a one-off test with no ongoing monitoring",
                    "They mentioned monitoring, but it sounds like a one-off, static test",
                    "No — this is a static, one-time test with no plan to check it over time",
                    "I'm not sure — I haven't asked whether they monitor for changes over time",
                ),
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
                    "Does the metric they're showing you actually match the business outcome "
                    "you need — or did they pick a metric because it looks good, not because it's "
                    "what you care about?"
                ),
                "minor_weight": 1.0,
                "example_good": "They explain why the chosen metric (e.g. cost saved, not just accuracy) maps to what you actually care about.",
                "example_bad": "They lead with a flattering metric (e.g. 99% accuracy) that doesn't reflect the outcome you're paying for.",
                "combined_options": _opts(
                    "Yes — they documented why this metric maps to the business outcome we care about",
                    "Yes — they explained the metric choice, but didn't document the reasoning",
                    "They gave documentation, but the metric still doesn't clearly map to our business outcome",
                    "They said something about the metric choice, but it still looks like a flattering number, not our outcome",
                    "No — they wouldn't explain why this metric is the right one for us",
                    "I'm not sure — I haven't asked why this metric was chosen",
                ),
            },
            {
                "id": "d5_q2",
                "script": "Was the pass/fail threshold agreed before they saw the results, or chosen afterwards to fit the number they got?",
                "minor_weight": 1.0,
                "example_good": "They show a dated protocol or sign-off where the pass/fail bar was agreed before the test ran.",
                "example_bad": "The threshold conveniently matches whatever number they got, with no prior agreement on record.",
                "combined_options": _opts(
                    "Yes — they showed a dated protocol proving the threshold was agreed before the test ran",
                    "Yes — they said the threshold was set in advance, but gave no documentation",
                    "They gave documentation, but it doesn't clearly show the threshold was set before results were seen",
                    "They said the threshold was set in advance, but it conveniently matches the number they got",
                    "No — they wouldn't say when or how the threshold was set",
                    "I'm not sure — I haven't asked when the threshold was set",
                ),
            },
            {
                "id": "d5_q3",
                "script": "Did they compare against a baseline or simplest-possible-approach, or is this number presented with nothing to compare it to?",
                "minor_weight": 1.0,
                "example_good": "They show performance against a simple baseline or the next-best alternative, so you can see the actual lift.",
                "example_bad": "The number is presented on its own, with nothing to compare it against.",
                "combined_options": _opts(
                    "Yes — they documented a comparison against a baseline or simpler alternative",
                    "Yes — they said there's a baseline comparison, but didn't show it",
                    "They gave documentation, but there's still no real baseline comparison in it",
                    "They mentioned a baseline, but never actually showed the comparison",
                    "No — the number is presented with nothing to compare it against",
                    "I'm not sure — I haven't asked whether there's a baseline comparison",
                ),
            },
            {
                "id": "d5_q4",
                "script": "Did they test against tricky edge cases, or only the easy ones?",
                "minor_weight": 0.5,
                "example_good": "They include adversarial or unusual examples in the test set, not just the easy majority cases.",
                "example_bad": "The test set is all straightforward, typical cases — nothing that would actually stress the model.",
                "combined_options": _opts(
                    "Yes — they documented testing against adversarial or edge-case examples",
                    "Yes — they said they tested edge cases, but didn't show the results",
                    "They gave documentation, but it's still mostly easy, typical cases",
                    "They mentioned edge cases, but the examples shown are all easy ones",
                    "No — only easy, typical cases were tested, as far as we can tell",
                    "I'm not sure — I haven't asked whether edge cases were tested",
                ),
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
                "script": "Is there any overlap between the data they trained on and the data they tested on — same stores, same time period, same source?",
                "minor_weight": 1.0,
                "example_good": "They list the specific stores/time periods excluded from training and show how overlap was checked (e.g. a dedup log by store ID).",
                "example_bad": "They say “we made sure there's no overlap” with no specifics on how.",
                "combined_options": _opts(
                    "Yes — they documented exactly which stores/periods were excluded from training, with proof of no overlap",
                    "Yes — they said there's no overlap, but gave no documentation",
                    "They gave documentation, but it doesn't clearly rule out overlap between training and test data",
                    "They said there's no overlap, but couldn't explain how they checked",
                    "No — they wouldn't confirm whether training and test data overlap",
                    "I'm not sure — I haven't asked whether training and test data overlap",
                ),
            },
            {
                "id": "d6_q2",
                "script": "Did they check for and remove near-duplicate records between training and test data?",
                "minor_weight": 1.0,
                "example_good": "They describe a specific method (e.g. similarity threshold on embeddings) and share the dedup results.",
                "example_bad": "They say they “don't think there are duplicates.”",
                "combined_options": _opts(
                    "Yes — they documented a specific deduplication method and shared the results",
                    "Yes — they said they checked for duplicates, but gave no documentation",
                    "They gave documentation, but it doesn't show a real deduplication check",
                    "They said they “don't think there are duplicates,” with no real check described",
                    "No — they wouldn't say whether they checked for near-duplicates",
                    "I'm not sure — I haven't asked whether they checked for near-duplicates",
                ),
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
                "script": "Did they show you where it failed, or only where it succeeded?",
                "minor_weight": 1.0,
                "example_good": "They walk you through specific cases where the model got it wrong, not just the wins.",
                "example_bad": "Every example they show is a success — no failure cases anywhere in the material.",
                "combined_options": _opts(
                    "Yes — they documented specific failure cases, not just successes",
                    "Yes — they said there are failure cases, but didn't show any",
                    "They gave documentation, but it's still mostly success stories, few real failures",
                    "They mentioned failures exist, but every example shown was a success",
                    "No — every example shown was a success, no failure cases at all",
                    "I'm not sure — I haven't asked to see failure cases",
                ),
            },
            {
                "id": "d7_q2",
                "script": "Is there a written limitations section, or is this presented as flawless?",
                "minor_weight": 1.0,
                "example_good": "There's a written section listing where the model is known to underperform or hasn't been tested.",
                "example_bad": "The evaluation is presented as flawless, with no caveats or limitations mentioned.",
                "combined_options": _opts(
                    "Yes — there's a written limitations section covering where this doesn't apply",
                    "Yes — they said there are limitations, but nothing is written down",
                    "There's some documentation, but it doesn't really cover limitations or caveats",
                    "They mentioned some limitations verbally, but nothing substantive",
                    "No — this is presented as flawless, with no limitations mentioned",
                    "I'm not sure — I haven't asked for a limitations section",
                ),
            },
            {
                "id": "d7_q3",
                "script": "Is there enough detail here that an independent person could rerun this evaluation and get the same answer?",
                "minor_weight": 1.0,
                "example_good": "They share enough detail — data sources, split logic, parameters — that someone else could rerun it and check.",
                "example_bad": "There's no way to reproduce this; you just have to take the summary number on faith.",
                "combined_options": _opts(
                    "Yes — they shared enough detail (data sources, splits, parameters) that this could be reproduced",
                    "Yes — they said it's reproducible, but didn't actually share the details",
                    "They gave documentation, but it's not enough detail to actually reproduce this",
                    "They said it could be reproduced, but didn't share anything concrete",
                    "No — there's no way to reproduce this; we'd just have to take the number on faith",
                    "I'm not sure — I haven't asked for enough detail to reproduce this",
                ),
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
# Used both for "vendor wouldn't say" (re-ask/push back) and "not yet asked"
# (ask for the first time) — the request to the vendor reads the same either way.

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
# In this scenario the buyer did run the stress test conversation with the
# vendor — every gap below is something the vendor was asked and didn't
# provide, not something the buyer forgot to ask.

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
            "d2_q2": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
        },
        "d3_percase": {
            "d3_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d3_q2": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
        },
        "d4_temporal": {
            "d4_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d4_q2": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
        },
        "d5_metric": {
            "d5_q1": {"score_key": "inadequate", "evidence": "Self-reported by vendor"},
            "d5_q2": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
            "d5_q3": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
            "d5_q4": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
        },
        "d6_leakage": {
            "d6_q1": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
            "d6_q2": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
        },
        "d7_transparency": {
            "d7_q1": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
            "d7_q2": {"score_key": "withheld", "evidence": "Vendor wouldn't say"},
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
