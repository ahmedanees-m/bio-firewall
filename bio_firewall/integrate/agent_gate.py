"""The pre-action gate + a guarded synthesis action + a gated agent loop. This is the concrete realisation of the
'design-stage, in-workflow, can't-route-around-it' claim: a design agent calls `pre_action_gate(plan)` before any
downstream action, and `synthesize()` REFUSES to run unless handed an `allow` verdict whose passport verifies."""
from __future__ import annotations

from bio_firewall.access.managed import access_resolution, resolution_permits_execution
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
    verdict with a verifiable passport whose managed-access resolution releases it - so a flagged/refused plan, a
    forged passport, or a plan held by the access plane cannot reach synthesis."""
    if verdict.get("decision") != "allow":
        raise GateBlocked(f"blocked: BioFirewall verdict is '{verdict.get('decision')}' - {verdict.get('reason')}")
    if not verify_passport(verdict.get("passport") or {}):
        raise GateBlocked("blocked: design passport does not verify (tampered or missing)")
    # An out-of-KB allow held for an unverified requester still carries decision "allow", so the decision
    # alone does not settle whether the action may run; the access resolution does.
    resolution = access_resolution(verdict)
    if not resolution_permits_execution(resolution):
        raise GateBlocked(f"blocked: managed-access resolution is '{resolution}', which withholds release")
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
        except Exception as e:                      # a gate that errors must block, never let a plan through
            outcome = f"blocked: gate error - {type(e).__name__}: {e}"
        trace.append({
            "step": i, "plan_intent": plan.get("intent", ""),
            "decision": verdict["decision"], "confidence": verdict.get("calibrated_confidence"),
            "reason": verdict.get("reason"), "axes_triggered": [f["axis"] for f in verdict.get("evidence", [])],
            "reached_synthesis": executed, "outcome": outcome,
        })
    return trace
