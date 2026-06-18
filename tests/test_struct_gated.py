"""WS-STRUCT-GATED (v0.8.0): the confidence-gated fusion fuses the fold channel ONLY where pLDDT is high and defers
to ESM elsewhere, so it cannot dilute ESM at the operating point. Synthetic + CI-safe; the real <=40%-id holdout
head-to-head is eval/cargo_bench/struct_gated_bench.py (VM)."""
from __future__ import annotations

import numpy as np

from bio_firewall.hazard.struct_channel import confidence_gated_score, normalize01, tpr_at_fpr


def test_gated_equals_esm_where_low_confidence():
    esm = np.array([0.1, 0.9, 0.2, 0.8])
    struct = np.array([5.0, 1.0, 9.0, 2.0])
    plddt = np.array([10.0, 20.0, 30.0, 40.0])               # all below threshold -> defer to ESM everywhere
    g = confidence_gated_score(esm, struct, plddt, plddt_min=70.0)
    assert np.allclose(g, normalize01(esm))


def test_gated_fuses_only_high_confidence_entries():
    esm = np.array([0.1, 0.9, 0.2, 0.8])
    struct = np.array([0.0, 1.0, 0.0, 1.0])
    plddt = np.array([90.0, 90.0, 10.0, 10.0])
    g = confidence_gated_score(esm, struct, plddt, plddt_min=70.0)
    e, s = normalize01(esm), normalize01(struct)
    assert np.allclose(g[:2], 0.5 * (e[:2] + s[:2]))         # high-confidence -> fused
    assert np.allclose(g[2:], e[2:])                         # low-confidence -> ESM alone


def test_gating_does_not_dilute_when_structure_is_noise():
    rng = np.random.RandomState(0)
    n = 200
    y = np.r_[np.zeros(n), np.ones(n)].astype(int)
    esm = np.r_[rng.normal(0.3, 0.1, n), rng.normal(0.7, 0.1, n)]    # informative
    struct = rng.normal(0.5, 0.3, 2 * n)                            # pure noise
    plddt = rng.uniform(0, 60, 2 * n)                               # all LOW confidence -> defer to ESM
    g = confidence_gated_score(esm, struct, plddt, plddt_min=70.0)
    assert tpr_at_fpr(y, g) == tpr_at_fpr(y, normalize01(esm))       # no dilution: identical to ESM ranking
