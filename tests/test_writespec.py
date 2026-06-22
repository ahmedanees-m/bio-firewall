"""WS-WRITESPEC (v0.9.1): screening a typed WriteRequest matches the dict path on the same design, and a
hazard-relevant unresolved field yields a scope flag (never a silent allow). The mapping is duck-typed, so the core
tests use WriteRequest-shaped dicts; one test exercises a real pen_stack.spec.WriteRequest."""
from __future__ import annotations

import pytest

from bio_firewall import screen
from bio_firewall.adapters.writespec import screen_writerequest, writerequest_to_plan
from bio_firewall.audit.log import AuditLog

_BENIGN = {"write_type": "insertion", "target": {"kind": "gene", "gene": {"label": "AAVS1"}},
           "cargo": [{"name": "FIX", "role": {"label": "therapeutic cassette"}}],
           "cell_type": {"label": "hepatocyte"}, "free_text_note": "insert FIX at AAVS1"}
_ONCO = {"write_type": "insertion", "target": {"kind": "gene", "gene": {"label": "LMO2"}},
         "cargo": [{"name": "GFP", "role": {"label": "reporter"}}], "cell_type": {"label": "hspc"}}
_EMBRYO = {"write_type": "insertion", "target": {"kind": "gene", "gene": {"label": "AAVS1"}},
           "cargo": [{"name": "GFP", "role": {"label": "reporter"}}], "cell_type": {"label": "embryo"}}
_UNRESOLVED = {"write_type": "insertion", "cargo": [{"name": "GFP", "role": {"label": "reporter"}}]}   # no target


def test_benign_resolved_allows_no_scope_flag():
    v = screen_writerequest(_BENIGN)
    assert v["decision"] == "allow"
    assert v["writespec"]["unresolved_hazard_fields"] == []


def test_oncogene_locus_flags():
    v = screen_writerequest(_ONCO)
    assert v["decision"] == "flag_for_review"
    assert v["axes"]["locus"]["decision"] != "clear"


def test_embryo_cell_type_flags_germline():
    v = screen_writerequest(_EMBRYO)
    assert v["decision"] == "flag_for_review" and v["axes"]["germline"]["decision"] != "clear"


def test_unresolved_locus_scope_flag_never_silent_allow():
    plan, unresolved = writerequest_to_plan(_UNRESOLVED)
    assert unresolved == ["locus"]
    v = screen_writerequest(_UNRESOLVED)
    assert v["decision"] == "flag_for_review"                 # escalated from allow
    assert "scope_flag" in v["writespec"] and "locus" in v["writespec"]["unresolved_hazard_fields"]


def test_concordance_with_dict_path():
    wr_decision = screen_writerequest(_ONCO)["decision"]
    dict_decision = screen({"intent": "insertion", "gene": "LMO2", "cell_type": "hspc"})["decision"]
    assert wr_decision == dict_decision == "flag_for_review"


def test_audit_logs_writespec_screen():
    log = AuditLog()
    screen_writerequest(_UNRESOLVED, audit=log)
    assert log.verify()
    assert any(e["record"].get("event") == "writespec_screen" for e in log.entries)


def test_real_writerequest_round_trip():
    try:
        from pen_stack.spec import CargoComponent, Resolved, Target, WriteRequest
        wr = WriteRequest(write_type="insertion",
                          target=Target(kind="gene", gene=Resolved(text="LMO2", label="LMO2")),
                          cargo=[CargoComponent(name="GFP", role=Resolved(text="reporter", label="reporter"))],
                          cell_type=Resolved(text="hspc", label="hspc"))
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"pen_stack.spec.WriteRequest not constructible here: {e}")
    assert screen_writerequest(wr)["decision"] == "flag_for_review"   # LMO2 locus flag, via the real typed object
