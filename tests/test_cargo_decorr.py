"""Unit tests for the WS-CARGO-DECORR helpers (composition matching + bootstrap math). Synthetic data, no torch/
esm/bf_b2 needed - the DANN head + the full run() execute on the VM with the frozen Benchmark-2 vectors. Here we
just verify the matching and the permutation test are correct, so the headline 'composition-matched' claim is sound."""
from __future__ import annotations

import numpy as np

from bio_firewall.eval.cargo_bench.decorr import (
    aa_comp, cluster_boot, energy_pvalue, match_negatives, tpr_at_fpr,
)


def test_aa_comp_is_a_frequency_vector():
    c = aa_comp("ACDEFGHIKLMNPQRSTVWY" * 3)
    assert c.shape == (20,)
    assert abs(c.sum() - 1.0) < 1e-9
    assert np.allclose(c, 1 / 20)               # uniform sequence -> uniform composition


def test_tpr_at_fpr_perfect_and_random():
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    assert tpr_at_fpr(y, np.array([0.0, 0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 1.0])) == 1.0
    rng = np.random.RandomState(0)
    yr = np.array([0] * 500 + [1] * 500)
    assert tpr_at_fpr(yr, rng.rand(1000)) < 0.2


def test_energy_pvalue_separates_same_from_different():
    rng = np.random.RandomState(0)
    A = rng.normal(0, 1, (60, 20))
    B = rng.normal(0, 1, (60, 20))               # same distribution -> indistinguishable
    C = rng.normal(3, 1, (60, 20))               # shifted -> distinguishable
    assert energy_pvalue(A, B, reps=300)[1] > 0.05
    assert energy_pvalue(A, C, reps=300)[1] < 0.05


def test_matching_makes_negatives_indistinguishable_from_positives():
    """Greedy composition matching should select a benign subset whose composition matches the positives - i.e.
    the energy-distance p-value rises above 0.05 after matching (it was < 0.05 against the full off-distribution pool)."""
    rng = np.random.RandomState(1)
    pos = rng.normal(0.0, 1.0, (40, 20))
    near = rng.normal(0.0, 1.0, (200, 20))       # benigns overlapping the positives
    far = rng.normal(4.0, 1.0, (200, 20))        # benigns clearly off-distribution
    neg = np.vstack([near, far])
    p_before = energy_pvalue(pos, neg, reps=300)[1]
    idx, _ = match_negatives(pos, neg, k=3)
    p_after = energy_pvalue(pos, neg[idx], reps=300)[1]
    assert p_before < 0.05 < p_after
    assert all(i < 200 for i in idx)             # matching prefers the overlapping (near) benigns, not the far ones


def test_cluster_boot_returns_valid_interval():
    rng = np.random.RandomState(2)
    y = np.array([0] * 50 + [1] * 50)
    p = np.concatenate([rng.rand(50) * 0.6, 0.4 + rng.rand(50) * 0.6])
    clusters = np.arange(100) % 20             # 20 clusters
    lo, hi = cluster_boot(y, p, clusters, tpr_at_fpr, reps=300)
    assert 0.0 <= lo <= hi <= 1.0
