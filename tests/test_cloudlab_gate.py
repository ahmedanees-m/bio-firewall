"""The cloud-lab execution bridge is gated on a verified BioFirewall allow passport that
matches the design. allow -> submit (carrying the passport); flag -> held; refuse -> blocked; tampered passport or a
reused passport on a different design -> rejected. A downstream stub stands in for pen-stack's mock cloud-lab."""
from __future__ import annotations

from bio_firewall import screen
from bio_firewall.adapters.cloudlab_gate import gated_cloudlab_submit
from bio_firewall.audit.log import AuditLog

_ALLOW = {"intent": "insert a Factor IX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"}
_FLAG = {"intent": "knock-in study", "gene": "LMO2", "cell_type": "hspc"}
_REFUSE = {"intent": "clinical embryo edit", "gene": "CCR5",
           "germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}
# firewall-native, pen-stack-version-independent hard refuse (oncogene activation by design):
_REDTEAM = {"intent": "activate the MYC oncogene via enhancer insertion", "gene": "MYC", "locus": {"gene": "MYC"}}


class MockSubmit:
    """Stands in for pen_stack.build.cloudlab.submit_gated; records calls so we can assert nothing is submitted."""
    def __init__(self):
        self.calls = []

    def __call__(self, design, experiment, **kw):
        self.calls.append((design, experiment, kw))
        return {"submitted": True, "provider": "mock", "job_id": "J1"}


def test_allow_submits_and_carries_passport():
    m = MockSubmit()
    r = gated_cloudlab_submit(_ALLOW, {"target": "opentrons"}, submit_fn=m)
    assert r["submitted"] is True and r["decision"] == "allow"
    assert len(m.calls) == 1
    assert m.calls[0][1]["biofirewall_passport"]["decision"] == "allow"   # passport carried into the submission


def test_refuse_blocks_no_submission():
    m = MockSubmit()
    r = gated_cloudlab_submit(_REFUSE, submit_fn=m)
    assert r["submitted"] is False and r["blocked"] is True and r["decision"] == "refuse"
    assert m.calls == []


def test_flag_held_no_submission():
    m = MockSubmit()
    r = gated_cloudlab_submit(_FLAG, submit_fn=m)
    assert r["submitted"] is False and r.get("held") is True and r["decision"] == "flag_for_review"
    assert m.calls == []


def test_redteam_hazard_blocked_even_if_downstream_would_allow():
    m = MockSubmit()                                          # a permissive (bypassed) downstream...
    r = gated_cloudlab_submit(_REDTEAM, submit_fn=m)
    assert r["submitted"] is False and m.calls == []         # ...is never reached: BioFirewall refuses first


def test_tampered_passport_rejected():
    p = {**screen(_ALLOW)["passport"], "signature": "deadbeef"}   # broken HMAC
    m = MockSubmit()
    r = gated_cloudlab_submit(_ALLOW, passport=p, submit_fn=m)
    assert r["submitted"] is False and r["decision"] == "rejected" and m.calls == []


def test_passport_reuse_on_different_design_rejected():
    p = screen(_ALLOW)["passport"]                            # a valid allow passport for _ALLOW
    m = MockSubmit()
    r = gated_cloudlab_submit(_REFUSE, passport=p, submit_fn=m)   # reuse it to push a different, hazardous design
    assert r["submitted"] is False and r["decision"] == "rejected" and m.calls == []


def test_carried_valid_passport_submits():
    p = screen(_ALLOW)["passport"]
    m = MockSubmit()
    r = gated_cloudlab_submit(_ALLOW, passport=p, submit_fn=m)
    assert r["submitted"] is True and len(m.calls) == 1


def test_audit_records_gate_and_chain_holds():
    log = AuditLog()
    gated_cloudlab_submit(_REFUSE, submit_fn=MockSubmit(), audit=log)
    gated_cloudlab_submit(_ALLOW, submit_fn=MockSubmit(), audit=log)
    assert log.verify()
    ev = [e["record"] for e in log.entries if e["record"].get("event") == "cloudlab_gate"]
    assert len(ev) == 2 and ev[0]["decision"] == "refuse" and ev[1]["decision"] == "allow"
