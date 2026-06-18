"""The pre-action gate + a guarded synthesis action + a gated agent loop. This is the concrete realisation of the
'design-stage, in-workflow, can't-route-around-it' claim: a design agent calls `pre_action_gate(plan)` before any
downstream action, and `synthesize()` REFUSES to run unless handed an `allow` verdict whose passport verifies."""
from __future__ import annotations

from bio_firewall.intercept.spine import screen
from bio_firewall.passport import verify_passport


class GateBlocked(Exception):
    """Raised when a downstream action is attempted without a passing BioFirewall verdict."""


def pre_action_gate(artifact: dict, audit=None) -> dict:
    """The hook a design agent MUST call before executing/ordering a plan. Returns the verdict; the agent proceeds
    only if `verdict['decision'] == 'allow'`. Pass an AuditLog to record the (plan, verdict) in the tamper-evident chain."""
    return screen(artifact, audit=audit)


def synthesize(verdict: dict) -> str:
    """A guarded downstream action (stand-in for a synthesis order / protocol export). It runs ONLY on an ALLOW
    verdict with a verifiable passport — so a flagged/refused plan, or a forged passport, cannot reach synthesis."""
    if verdict.get("decision") != "allow":
        raise GateBlocked(f"blocked: BioFirewall verdict is '{verdict.get('decision')}' — {verdict.get('reason')}")
    if not verify_passport(verdict.get("passport") or {}):
        raise GateBlocked("blocked: design passport does not verify (tampered or missing)")
    return "SYNTHESIS ORDER SUBMITTED"


def run_gated_loop(plans, audit=None) -> list[dict]:
    """Run an iterable of agent-proposed artifacts through the gate. Each plan reaches synthesis ONLY if it passes;
    returns a trace recording the verdict, whether the downstream action executed, and why."""
    trace: list[dict] = []
    for i, plan in enumerate(plans):
        verdict = pre_action_gate(plan, audit=audit)
        executed, outcome = False, None
        try:
            outcome = synthesize(verdict)
            executed = True
        except GateBlocked as e:
            outcome = str(e)
        trace.append({
            "step": i, "plan_intent": plan.get("intent", ""),
            "decision": verdict["decision"], "confidence": verdict.get("calibrated_confidence"),
            "reason": verdict.get("reason"), "axes_triggered": [f["axis"] for f in verdict.get("evidence", [])],
            "reached_synthesis": executed, "outcome": outcome,
        })
    return trace
