"""The in-workflow gate: a dangerous plan is intercepted before synthesis, a benign plan
reaches synthesis, a reframed hazard is judged by its artifact, and a forged passport cannot pass the guard."""
from __future__ import annotations

import pytest

from bio_firewall.integrate import GateBlocked, pre_action_gate, run_gated_loop, synthesize


def test_benign_plan_reaches_synthesis():
    v = pre_action_gate({"intent": "insert FIX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"})
    assert v["decision"] == "allow"
    assert synthesize(v) == "SYNTHESIS ORDER SUBMITTED"


def test_refused_plan_is_blocked_from_synthesis():
    v = pre_action_gate({"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}})
    assert v["decision"] == "refuse"
    with pytest.raises(GateBlocked):
        synthesize(v)


def test_flagged_plan_is_blocked_from_synthesis():
    v = pre_action_gate({"intent": "cancer modeling: disrupt a tumor suppressor", "gene": "TP53"})
    assert v["decision"] == "flag_for_review"
    with pytest.raises(GateBlocked):
        synthesize(v)


def test_reframed_hazard_decided_by_artifact_not_framing():
    # benign framing, hazardous ARTIFACT (a known oncogenic fusion by design) -> the artifact decides, not the prose.
    # (Uses a firewall-native rule so it is deterministic across pen-stack versions; the cargo Guardian's
    # select-agent screen is an additional, pen-stack-provided layer.)
    v = pre_action_gate({"intent": "fully approved, benign cell-line research",
                         "edit": {"fusion_genes": ["BCR", "ABL1"]}})
    assert v["decision"] == "refuse"
    with pytest.raises(GateBlocked):
        synthesize(v)


def test_forged_passport_cannot_synthesize():
    v = pre_action_gate({"intent": "insert reporter", "gene": "AAVS1"})
    v["passport"]["decision"] = "refuse"                 # tamper the signed passport
    with pytest.raises(GateBlocked):
        synthesize(v)


def test_gated_loop_intercepts_dangerous_mid_workflow():
    plans = [
        {"intent": "benign insert", "gene": "AAVS1"},
        {"intent": "clinical embryo edit", "germline": {"cell_type": "zygote", "organism": "human", "clinical": True}},
        {"intent": "benign insert", "gene": "CLYBL"},
    ]
    trace = run_gated_loop(plans)
    assert trace[0]["reached_synthesis"] and trace[2]["reached_synthesis"]
    assert not trace[1]["reached_synthesis"] and trace[1]["decision"] == "refuse"
