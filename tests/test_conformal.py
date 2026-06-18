"""Unit tests for the WS-CONFORMAL machinery (the false-refuse certificate + Mondrian reliability + monotonicity +
selective curve). Pure stats, no torch/esm/COSMIC needed - the full corpus run is on the VM (conformal_bench)."""
from __future__ import annotations

from bio_firewall.calibrate.conformal import (
    clopper_pearson_upper, confidence_monotonicity, false_refuse_certificate,
    mondrian_reliability, selective_curve,
)


def test_clopper_pearson_zero_events_tightens_with_n():
    """With 0 observed refusals, the upper bound must shrink as n grows (more evidence -> tighter ceiling)."""
    assert clopper_pearson_upper(0, 10) > clopper_pearson_upper(0, 100) > clopper_pearson_upper(0, 1000)
    # 0/300 at 95% -> ~0.0099 (the regime that certifies a <=0.03 ceiling)
    assert 0.009 < clopper_pearson_upper(0, 300) < 0.011
    assert clopper_pearson_upper(5, 100) > clopper_pearson_upper(0, 100)   # more events -> looser


def test_false_refuse_certificate_passes_when_zero_of_many():
    cert = false_refuse_certificate(n_legit=288, n_refused=0)
    assert cert["all_pass"] is True
    assert cert["certified_upper_bound"] < 0.03
    for c in cert["coverage_curve"]:
        assert c["certified_upper_bound"] <= c["alpha"] + 0.02 + 1e-9


def test_false_refuse_certificate_fails_with_high_refusal():
    cert = false_refuse_certificate(n_legit=20, n_refused=8)         # 40% refusal (the over-refusing LLM regime)
    assert cert["all_pass"] is False
    assert cert["empirical_false_refuse"] == 0.4


def test_mondrian_reliability_partitions_by_decision():
    rows = [{"decision": "allow", "correct": True}, {"decision": "allow", "correct": False},
            {"decision": "flag_for_review", "correct": True}, {"decision": "refuse", "correct": True}]
    m = mondrian_reliability(rows)
    assert m["allow"]["n"] == 2 and m["allow"]["reliability"] == 0.5
    assert m["refuse"]["reliability"] == 1.0


def test_confidence_monotonicity_detects_monotone_and_inverted():
    mono = [{"conf": "high", "correct": True}] * 9 + [{"conf": "high", "correct": False}] \
        + [{"conf": "moderate", "correct": True}] * 6 + [{"conf": "moderate", "correct": False}] * 4 \
        + [{"conf": "low", "correct": False}] * 9 + [{"conf": "low", "correct": True}]
    assert confidence_monotonicity(mono)["monotone_high_ge_moderate_ge_low"] is True
    inverted = [{"conf": "high", "correct": False}] * 6 + [{"conf": "high", "correct": True}] * 4 \
        + [{"conf": "moderate", "correct": True}] * 9 + [{"conf": "moderate", "correct": False}]
    assert confidence_monotonicity(inverted)["monotone_high_ge_moderate_ge_low"] is False


def test_selective_curve_trades_miss_for_escalation():
    # risk low for benigns, high for hazards -> a mid threshold should auto-allow benigns and escalate hazards.
    risks = [0.0, 0.05, 0.1, 0.5, 0.6, 0.9]
    hazard = [0, 0, 0, 1, 1, 1]
    curve = selective_curve(risks, hazard, n_steps=11)
    assert curve[0]["auto_allow_frac"] == 0.0          # tau=0 -> nothing auto-allowed
    assert curve[-1]["miss_rate"] >= curve[0]["miss_rate"]   # higher tau -> auto-allow more -> more misses
