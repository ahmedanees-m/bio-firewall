"""Integration logic (P2.combine): stratify the five-axis findings into one verdict.

Stratification, NOT a blocklist (almost every hazardous genome-write is also legitimate research):
  - any `hard_reject`              -> REFUSE   (the unambiguous: select-agent cargo, human heritable clinical, ...)
  - else any soft_penalty/scope_flag -> FLAG-FOR-REVIEW with the evidence (routed to human oversight)
  - else                           -> ALLOW    (+ a signed passport)
Legality != confidence: the verdict carries the findings + a caveat note that the locus axis flags on mechanism.
"""
from __future__ import annotations

from bio_firewall.hazard.combine_mono import monotone_severity
from bio_firewall.hazard.finding import SEVERITY, Finding


def combine(findings: list[Finding]) -> dict:
    worst = max(findings, key=lambda f: SEVERITY[f.decision]) if findings else None
    # a provably-monotone, interaction-aware combiner (noisy-OR over per-axis risks, any hard_reject pinned to
    # refuse). Its DECISION equals the max-severity cascade (so behaviour is unchanged); it additionally surfaces
    # a continuous, auditable `severity` that escalates co-occurring moderate signals.
    severity, decision = monotone_severity(findings)
    triggered = [f.as_dict() for f in findings if f.decision != "clear"]
    return {
        "decision": decision,
        "severity": severity,
        "axes": {f.axis: f.as_dict() for f in findings},
        "evidence": triggered,
        "caveat": ("stratified risk, not a blocklist; the locus axis flags on MECHANISM (the genotoxicity proxy is "
                    "NOT outcome-validated, PEN-STACK) and does not predict a cancer rate; screening reduces, "
                    "does not eliminate; safe proxies != real hazards."),
        "reason": (worst.mechanism if worst and worst.decision != "clear" else "no hazard signal across the five axes"),
    }
