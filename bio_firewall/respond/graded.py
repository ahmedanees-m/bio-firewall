"""WS-GRADED (v0.8.0): formalize the stratified verdict into an explicit, tested taxonomy and gate the `partial`
tier's content.

  allow            : no hazard signal -> the full response + a signed passport.
  partial          : a single low-severity, research-context MECHANISM flag -> GENERAL context (why it is flagged +
                     a pointer to oversight) with NO actionable/operational detail.
  flag_for_review  : a scope-level flag, a sensitive axis (cargo / germline), or co-occurring flags -> held for
                     human oversight; general info is NOT auto-released.
  refuse           : a hard rule fired -> refusal, no actionable content.

Grounding: "Let Them Down Easy! Contextual Effects of LLM Guardrails" (Zheng et al., Findings of EMNLP 2025,
arXiv:2506.00195) - partial compliance (general information without actionable detail) reduces negative user
perception by >50% versus a flat refusal while preserving safety.

The mapping from the per-axis findings is DETERMINISTIC and TOTAL (no new judgment layer). The content gate is a
deterministic check (regex over actionable-detail signatures), not an LLM.
"""
from __future__ import annotations

import re

GRADES = ("allow", "partial", "flag_for_review", "refuse")

# Axes where even general context is held for human oversight rather than auto-released as `partial`:
#   cargo   - the hazardous-FUNCTION axis (the most sensitive cargo claim).
#   germline- heritable / policy-sensitive (IRB / ESCRO territory), regardless of severity.
_SENSITIVE_AXES = {"cargo", "germline"}

# Actionable / operational-detail signatures. Their presence in a `partial` response means it leaked beyond general
# context and the gate FAILS. Deterministic; no model. (General mechanism prose + gene symbols do not match these.)
_ACTIONABLE = [
    ("nucleotide_run", re.compile(r"\b[ACGTUacgtu]{12,}\b")),                  # an explicit >=12-base sequence
    ("genomic_coordinate", re.compile(r"\bchr[0-9XYMT]+\s*[:_-]\s*\d{3,}", re.I)),  # a specific chrom:coordinate
    ("five_prime_oligo", re.compile(r"5['\u2032]?\s*-\s*[ACGTU]{6,}", re.I)),  # a 5'-...primer / spacer oligo
    ("numbered_protocol", re.compile(r"\bstep\s*\d+\b", re.I)),                 # a step-by-step protocol
    ("restriction_site", re.compile(r"\b(?:GAATTC|GGATCC|AAGCTT|GGTACC|GAGCTC|TCTAGA|CTGCAG)\b")),  # named cut sites
]


def grade(verdict: dict) -> str:
    """Map a screened verdict to allow / partial / flag_for_review / refuse. Total over the decision domain;
    deterministic given the verdict's per-axis findings."""
    decision = verdict.get("decision")
    if decision in ("allow", "refuse"):
        return decision
    # decision == flag_for_review -> refine into partial vs flag
    flagged = [f for f in verdict.get("axes", {}).values() if f.get("decision") != "clear"]
    escalate = (any(f.get("decision") == "scope_flag" for f in flagged)        # a scope-level flag
                or len(flagged) > 1                                            # co-occurring flags (interaction risk)
                or any(f.get("axis") in _SENSITIVE_AXES for f in flagged))      # a sensitive axis
    return "flag_for_review" if escalate else "partial"


def _general_context(verdict: dict) -> str:
    """The general scientific context (WHY flagged) drawn from the firewall's own mechanism strings - no operational
    specifics. Mechanism prose carries gene symbols + risk class, never sequences/coordinates/protocols."""
    flagged = [f for f in verdict.get("axes", {}).values() if f.get("decision") != "clear"]
    return "; ".join(f"{f['axis']}: {f['mechanism']}" for f in flagged) or "a low-severity mechanism flag was raised"


def partial_response(verdict: dict) -> dict:
    """Build the `partial` response: general context + a pointer to oversight, with actionable/operational detail
    explicitly withheld. Passes the content gate by construction (it is built from general mechanism prose)."""
    return {
        "grade": "partial",
        "general_context": _general_context(verdict),
        "guidance": ("general scientific context is provided; operational / actionable detail (sequences, "
                     "coordinates, protocols) is withheld pending review"),
        "next_step": "route to human / IRB oversight for the flagged axis before any build step",
        "actionable_detail_withheld": True,
    }


def content_gate(response) -> dict:
    """Deterministically verify a `partial` response contains no actionable/operational detail. `response` may be the
    partial-response dict or a raw string. Returns {clean, violations}."""
    text = response if isinstance(response, str) else " ".join(str(v) for v in _values(response))
    violations = [name for name, rx in _ACTIONABLE if rx.search(text)]
    return {"clean": not violations, "violations": violations}


def _values(d: dict):
    for v in d.values():
        if isinstance(v, dict):
            yield from _values(v)
        else:
            yield v


def graded_response(verdict: dict) -> dict:
    """Attach the grade and, for a `partial` grade, the content-gated partial response. Does not mutate `verdict`."""
    g = grade(verdict)
    out = {"grade": g}
    if g == "partial":
        pr = partial_response(verdict)
        gate = content_gate(pr)
        if not gate["clean"]:
            # pre-committed fallback: never ship an ambiguous/leaky partial -> collapse to full review.
            return {"grade": "flag_for_review", "collapsed_from": "partial",
                    "reason": f"partial content gate failed ({gate['violations']}); collapsed to review"}
        out["partial_response"] = pr
        out["content_gate"] = gate
    return out
