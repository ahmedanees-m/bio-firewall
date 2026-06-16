"""Integration logic (P2.combine): stratify the five-axis findings into one verdict.

Stratification, NOT a blocklist (almost every hazardous genome-write is also legitimate research):
  - any `hard_reject`              -> REFUSE   (the unambiguous: select-agent cargo, human heritable clinical, ...)
  - else any soft_penalty/scope_flag -> FLAG-FOR-REVIEW with the evidence (routed to human oversight)
  - else                           -> ALLOW    (+ a signed passport, Phase 2)
Legality ≠ confidence: the verdict carries the findings + an honesty note that the locus axis flags on mechanism.
"""
from __future__ import annotations

from bio_firewall.hazard.finding import SEVERITY, Finding


def combine(findings: list[Finding]) -> dict:
    worst = max(findings, key=lambda f: SEVERITY[f.decision]) if findings else None
    sev = SEVERITY[worst.decision] if worst else 0
    if sev >= 3:
        decision = "refuse"
    elif sev >= 1:
        decision = "flag_for_review"
    else:
        decision = "allow"
    triggered = [f.as_dict() for f in findings if f.decision != "clear"]
    return {
        "decision": decision,
        "axes": {f.axis: f.as_dict() for f in findings},
        "evidence": triggered,
        "honesty": ("stratified risk, not a blocklist; the locus axis flags on MECHANISM (the genotoxicity proxy is "
                    "NOT outcome-validated, PEN-STACK v6.6) and does not predict a cancer rate; screening reduces, "
                    "does not eliminate; safe proxies ≠ real hazards."),
        "reason": (worst.mechanism if worst and worst.decision != "clear" else "no hazard signal across the five axes"),
    }
