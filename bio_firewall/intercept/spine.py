"""P1 — the governance spine. The public entry point: any design AI hands BioFirewall a genome-writing artifact;
BioFirewall normalizes it, runs the five-axis hazard screen, signs a design passport, optionally logs the verdict
to a tamper-evident audit, and returns a stratified verdict.

The gate: no downstream action (synthesis order, build) should execute without a passing verdict. `refuse` and
`flag_for_review` short-circuit the build; `allow` emits a SIGNED passport (P4) a synthesis provider can verify."""
from __future__ import annotations

from bio_firewall.adapters.generic_artifact import normalize
from bio_firewall.calibrate import calibrate
from bio_firewall.hazard import five_axis_screen
from bio_firewall.passport.sign import sign_passport

RULESET_VERSION = "0.3.0"


def screen(artifact: dict, *, audit=None) -> dict:
    """Govern a genome-writing artifact -> {decision, axes, evidence, reason, honesty, passport}.
    decision ∈ {allow, flag_for_review, refuse}. Framing does not decide — the artifact does (Guardian-stripped).
    Pass `audit=AuditLog(...)` to append a tamper-evident record of the (plan, verdict)."""
    plan = normalize(artifact)
    verdict = five_axis_screen(plan)
    verdict = calibrate(verdict)                     # P8: bind confidence + abstention (may escalate a low-conf allow)
    verdict["ruleset_version"] = RULESET_VERSION
    verdict["passport"] = sign_passport(plan, verdict)
    if audit is not None:
        audit.append({"inputs_hash": verdict["passport"]["inputs_hash"], "decision": verdict["decision"],
                      "axes_triggered": verdict["passport"]["axes_triggered"], "ruleset_version": RULESET_VERSION})
    return verdict
