"""The combined decision is the conservative meet of the BioFirewall verdict and
pen-stack's in-design SafetyVerdict; disagreements (the gates cover different scopes) are characterized, not hidden."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from bio_firewall.adapters.reconcile import conservative_meet, map_penstack_decision, reconcile
from bio_firewall.audit.log import AuditLog

_ALLOW = {"intent": "insert a Factor IX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"}
_REFUSE = {"intent": "clinical embryo edit", "gene": "CCR5",
           "germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}


def _sv(decision, hits=(), reason=""):
    return SimpleNamespace(decision=decision, hits=list(hits), reason=reason)


def test_mapping_and_conservative_meet_cross_product():
    assert map_penstack_decision("clear") == "allow"
    assert map_penstack_decision("flag") == "flag_for_review"
    assert map_penstack_decision("escalate") == "flag_for_review"
    assert map_penstack_decision("refuse") == "refuse"
    assert map_penstack_decision("???") == "flag_for_review"          # unknown -> conservative flag
    sev = {"allow": 1, "flag_for_review": 2, "refuse": 3}
    for a in sev:
        for b in sev:
            assert sev[conservative_meet(a, b)] == max(sev[a], sev[b])   # the meet is the stricter of the two


def test_both_clear_agree_allow():
    r = reconcile(_ALLOW, safety_gate_fn=lambda d, a: _sv("clear"))
    assert r["combined"] == "allow" and r["agree"] is True and r["disagreement_kind"] == "agree"


def test_penstack_refuse_firewall_allow_meets_refuse():
    r = reconcile(_ALLOW, safety_gate_fn=lambda d, a: _sv("refuse", hits=[{"kind": "function_flag"}], reason="toxin"))
    assert r["combined"] == "refuse" and r["agree"] is False and r["disagreement_kind"] == "penstack_stricter"
    assert r["penstack"]["hits"] == ["function_flag"]


def test_firewall_refuse_penstack_clear_meets_refuse_firewall_stricter():
    # germline-clinical: BioFirewall refuses on an axis pen-stack's in-design gate does not cover
    r = reconcile(_REFUSE, safety_gate_fn=lambda d, a: _sv("clear"))
    assert r["combined"] == "refuse" and r["disagreement_kind"] == "firewall_stricter"
    assert r["firewall"]["decision"] == "refuse"


def test_escalate_maps_to_flag():
    r = reconcile(_ALLOW, safety_gate_fn=lambda d, a: _sv("escalate"))
    assert r["combined"] == "flag_for_review" and r["penstack"]["mapped"] == "flag_for_review"


def test_audit_logs_reconcile_and_chain_holds():
    log = AuditLog()
    reconcile(_REFUSE, safety_gate_fn=lambda d, a: _sv("clear"), audit=log)
    assert log.verify()
    ev = [e["record"] for e in log.entries if e["record"].get("event") == "verify_reconcile"]
    assert ev and ev[0]["combined"] == "refuse" and ev[0]["disagreement_kind"] == "firewall_stricter"


def test_real_penstack_safety_gate_integration(tmp_path, monkeypatch):
    monkeypatch.setenv("PEN_STACK_SAFETY_AUDIT", str(tmp_path / "audit.log"))
    try:
        r = reconcile(_ALLOW)                                          # default = real pen_stack.safety.safety_gate
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"pen-stack safety_gate not runnable here: {e}")
    assert r["combined"] == conservative_meet(r["firewall"]["decision"], map_penstack_decision(r["penstack"]["decision"]))
