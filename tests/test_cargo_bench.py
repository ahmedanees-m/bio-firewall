"""Unit tests for the Benchmark-2 (cargo ML gate) metric helpers - synthetic data, no mmseqs/esm/torch needed.
The full pipeline (UniProt + MMseqs2 + ESM2-650M) runs on a GPU/CPU box with those tools; here we just verify the
deployment-operating-point metrics are correct so the headline TPR@1%FPR number is trustworthy."""
from __future__ import annotations

import numpy as np

from bio_firewall.eval.cargo_bench.run import _fpr_at_tpr, _tpr_at_fpr


def test_tpr_at_fpr_perfect_separation():
    """Perfectly separable scores -> TPR@1%FPR = 1.0."""
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    p = np.array([0.0, 0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 1.0])
    assert _tpr_at_fpr(y, p, fpr_target=0.01) == 1.0


def test_tpr_at_fpr_random_is_low():
    """Scores uncorrelated with labels -> TPR@1%FPR should be low (near the FPR target), not 1.0."""
    rng = np.random.RandomState(0)
    y = np.array([0] * 500 + [1] * 500)
    p = rng.rand(1000)
    assert _tpr_at_fpr(y, p, fpr_target=0.01) < 0.2


def test_fpr_at_tpr_perfect_separation():
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    p = np.array([0.0, 0.1, 0.2, 0.3, 0.7, 0.8, 0.9, 1.0])
    assert _fpr_at_tpr(y, p, tpr_target=0.95) == 0.0


def test_metrics_handle_empty_class():
    y = np.array([1, 1, 1])
    p = np.array([0.5, 0.6, 0.7])
    assert np.isnan(_tpr_at_fpr(y, p))   # no negatives -> undefined, not a crash
