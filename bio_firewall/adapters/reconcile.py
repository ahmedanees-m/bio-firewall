"""Reconcile PEN-STACK's in-design verdict with the BioFirewall five-axis verdict.

PEN-STACK exposes the in-design verdict as `pen_stack.safety.safety_gate(design) -> SafetyVerdict`
(decision in {clear, flag, refuse, escalate}); there is no top-level `pen_stack.verify()`. This adapter reconciles
that verdict with the BioFirewall verdict.

The combined decision is the CONSERVATIVE MEET: a refuse on either side refuses; a flag/escalate on either flags;
allow only if both clear/allow. The two gates cover DIFFERENT scopes - pen-stack's biosecurity/legality hooks versus
BioFirewall's locus-outcome / germline / scale / decomposition axes - so disagreement is EXPECTED and is
characterized, not hidden and not forced into false agreement.
"""
from __future__ import annotations

_SEVERITY = {"allow": 1, "flag_for_review": 2, "refuse": 3}
# pen-stack SafetyVerdict.decision -> the firewall's three-valued decision
_PS_MAP = {"clear": "allow", "flag": "flag_for_review", "escalate": "flag_for_review", "refuse": "refuse"}


def map_penstack_decision(decision: str | None) -> str:
    """Map a pen-stack SafetyVerdict decision to the firewall's vocabulary (unknown -> conservative flag)."""
    return _PS_MAP.get(decision or "", "flag_for_review")


def conservative_meet(a: str, b: str) -> str:
    """The stricter of two firewall-valued decisions (refuse > flag_for_review > allow)."""
    return a if _SEVERITY.get(a, 2) >= _SEVERITY.get(b, 2) else b


def _default_safety_gate(design, actor="anonymous"):
    from pen_stack.safety import safety_gate   # noqa: PLC0415 - lazy guarded coupling (optional dependency surface)
    return safety_gate(design, actor=actor)


def _summarize_hits(sv) -> list:
    hits = getattr(sv, "hits", None)
    if hits is None and isinstance(sv, dict):
        hits = sv.get("hits")
    return [getattr(h, "kind", None) or (h.get("kind") if isinstance(h, dict) else str(h)) for h in (hits or [])]


def reconcile(design: dict, *, safety_gate_fn=None, actor: str = "anonymous", audit=None) -> dict:
    """Run both gates, take the conservative meet, and characterize any disagreement. `safety_gate_fn(design, actor)`
    returns a pen-stack SafetyVerdict-like object exposing `.decision` (clear/flag/refuse/escalate); it defaults to
    pen_stack.safety.safety_gate. Does not raise on disagreement - it reports it."""
    from bio_firewall.intercept.spine import screen   # lazy: avoid the adapters<->spine import cycle
    safety_gate_fn = safety_gate_fn or _default_safety_gate

    fw = screen(design)
    fw_decision = fw["decision"]
    fw_axes = [e["rule_id"] for e in fw.get("evidence", [])]

    sv = safety_gate_fn(design, actor)
    ps_raw = getattr(sv, "decision", None) or (sv.get("decision") if isinstance(sv, dict) else None)
    ps_mapped = map_penstack_decision(ps_raw)
    ps_reason = getattr(sv, "reason", None) or (sv.get("reason") if isinstance(sv, dict) else None)

    combined = conservative_meet(fw_decision, ps_mapped)
    agree = fw_decision == ps_mapped
    if agree:
        kind = "agree"
    elif _SEVERITY[fw_decision] > _SEVERITY[ps_mapped]:
        kind = "firewall_stricter"        # BioFirewall covers an axis pen-stack's in-design gate does not
    else:
        kind = "penstack_stricter"        # pen-stack's biosecurity/legality hook caught something the firewall cleared

    out = {
        "combined": combined,
        "agree": agree,
        "disagreement_kind": kind,
        "firewall": {"decision": fw_decision, "axes": fw_axes},
        "penstack": {"decision": ps_raw, "mapped": ps_mapped, "reason": ps_reason, "hits": _summarize_hits(sv)},
    }
    if audit is not None:
        audit.append({"event": "verify_reconcile", "combined": combined, "firewall": fw_decision,
                      "penstack": ps_raw, "disagreement_kind": kind})
    return out
