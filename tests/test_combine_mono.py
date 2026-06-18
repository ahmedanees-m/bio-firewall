"""WS-COMBINE-MONO (v0.6.0) — the monotone, interaction-aware combiner: provably monotone, hard-rule-exact, and
decision-equivalent to the v0.5 cascade. Pure logic, no torch/pen_stack."""
from __future__ import annotations

import random

from bio_firewall.hazard.combine_mono import (
    decision_matches_cascade, monotone_severity, verify_monotone,
)


def _f(*decisions, rule_ids=None):
    rule_ids = rule_ids or [None] * len(decisions)
    return [{"decision": d, "rule_id": r} for d, r in zip(decisions, rule_ids)]


def test_verify_monotone_passes():
    rep = verify_monotone(reps=4000)
    assert rep["provably_monotone"] is True
    assert rep["monotone_under_addition"] and rep["monotone_under_upgrade"]
    assert rep["hard_rule_exact_refuse"] is True
    assert rep["n_hard"] > 0                              # the suite actually exercised hard_reject cases


def test_decisions_unchanged_vs_cascade():
    assert monotone_severity([]) == (0.0, "allow")
    assert monotone_severity(_f("soft_penalty"))[1] == "flag_for_review"
    assert monotone_severity(_f("scope_flag"))[1] == "flag_for_review"
    assert monotone_severity(_f("hard_reject")) == (1.0, "refuse")
    # a hard_reject dominates any number of soft signals
    assert monotone_severity(_f("soft_penalty", "scope_flag", "hard_reject")) == (1.0, "refuse")


def test_interaction_co_occurring_signals_escalate_severity():
    one = monotone_severity(_f("soft_penalty"))[0]
    three = monotone_severity(_f("soft_penalty", "soft_penalty", "soft_penalty"))[0]
    assert three > one                                    # noisy-OR rises with co-occurring signals (a max cannot)
    # ...but co-occurring SOFT signals never auto-refuse (flag-not-block is preserved)
    many = monotone_severity(_f(*(["scope_flag"] * 8)))
    assert many[1] == "flag_for_review" and many[0] < 0.90


def test_decision_equivalence_random():
    rng = random.Random(0)
    tiers = ["clear", "soft_penalty", "scope_flag", "hard_reject"]
    for _ in range(2000):
        fs = _f(*[rng.choice(tiers) for _ in range(rng.randint(0, 5))])
        assert decision_matches_cascade(fs)
