"""P1 — the governance spine. The public entry point: any design AI hands BioFirewall a genome-writing artifact;
BioFirewall normalizes it, runs the five-axis hazard screen, signs a design passport, optionally logs the verdict
to a tamper-evident audit, and returns a stratified verdict.

The gate: no downstream action (synthesis order, build) should execute without a passing verdict. `refuse` and
`flag_for_review` short-circuit the build; `allow` emits a SIGNED passport (P4) a synthesis provider can verify."""
from __future__ import annotations

from bio_firewall.adapters.generic_artifact import normalize
from bio_firewall.calibrate import calibrate
from bio_firewall.calibrate.conformal import calibrated_confidence, kb_coverage, risk_score
from bio_firewall.hazard import five_axis_screen
from bio_firewall.passport.sign import sign_passport

RULESET_VERSION = "0.5.0"


def screen(artifact: dict, *, audit=None) -> dict:
    """Govern a genome-writing artifact -> {decision, axes, evidence, reason, honesty, passport}.
    decision ∈ {allow, flag_for_review, refuse}. Framing does not decide — the artifact does (Guardian-stripped).
    Pass `audit=AuditLog(...)` to append a tamper-evident record of the (plan, verdict)."""
    plan = normalize(artifact)
    verdict = five_axis_screen(plan)
    verdict = calibrate(verdict)                     # P8: bind confidence + abstention (may escalate a low-conf allow)
    # v0.4.0 WS-CONFORMAL: surface the COMPETENCE-conditioned confidence + KB-coverage + continuous risk WITHOUT
    # changing the decision — a clean allow of a gene OUTSIDE the firewall's data is honestly LOW confidence (the
    # competence boundary), resolving the v0.3 tier inversion. The decision/abstain logic above is unchanged.
    _gene = str((plan.get("locus") or {}).get("gene") or plan.get("gene") or "")
    verdict["kb_coverage"] = kb_coverage(_gene)
    verdict["calibrated_confidence"] = calibrated_confidence(verdict, _gene)
    verdict["risk_score"] = risk_score(verdict, _gene)
    verdict["ruleset_version"] = RULESET_VERSION
    verdict["passport"] = sign_passport(plan, verdict)
    if audit is not None:
        audit.append({"inputs_hash": verdict["passport"]["inputs_hash"], "decision": verdict["decision"],
                      "axes_triggered": verdict["passport"]["axes_triggered"], "ruleset_version": RULESET_VERSION})
    return verdict
