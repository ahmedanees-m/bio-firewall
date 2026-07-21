"""The Neyman-Pearson conformal selector controls the false-selection rate at alpha
(finite-sample, via conformal p-values) and extracts MULTIVARIATE power a scalar threshold discards. Synthetic +
CI-safe; the firewall-corpus head-to-head is eval/hazard_bench/conformal_np_bench.py (VM)."""
from __future__ import annotations

import numpy as np

from bio_firewall.calibrate.conformal_np import (
    catch_rate,
    conformal_pvalues,
    false_select_rate,
    np_lr_select,
    power_gap_ci,
    scalar_threshold_select,
)


def test_conformal_pvalues_control_false_selection():
    rng = np.random.RandomState(1)
    calib = rng.normal(0, 1, 3000)
    test_null = rng.normal(0, 1, 3000)                         # test drawn from the SAME null
    p = conformal_pvalues(calib, test_null)
    for alpha in (0.05, 0.10, 0.20):
        assert (p <= alpha).mean() <= alpha + 0.03             # false-selection controlled at alpha


def test_np_lr_beats_scalar_when_signal_is_multivariate():
    rng = np.random.RandomState(0)
    n = 800
    Xtr = np.vstack([rng.normal(0, 1, (n, 2)), rng.normal(1.1, 1, (n, 2))])
    ytr = np.r_[np.zeros(n), np.ones(n)]
    Xcal = rng.normal(0, 1, (n, 2))                            # legitimate-null calibration
    Xte = np.vstack([rng.normal(0, 1, (n, 2)), rng.normal(1.1, 1, (n, 2))])
    haz = np.r_[np.zeros(n), np.ones(n)].astype(int)
    alpha = 0.10
    r = np_lr_select(Xtr, ytr, Xcal, Xte, alpha)
    base = scalar_threshold_select(Xcal[:, 0], Xte[:, 0], alpha)    # scalar collapse: feature 1 only
    assert false_select_rate(r["selected"], haz) <= alpha + 0.05
    assert false_select_rate(base, haz) <= alpha + 0.05
    assert catch_rate(r["selected"], haz) > catch_rate(base, haz)   # NP-LR recovers the 2nd-feature power


def test_power_gap_ci_shape():
    haz = np.r_[np.zeros(50), np.ones(50)].astype(int)
    sel_np = haz.astype(bool)
    sel_base = np.zeros(100, bool)
    r = power_gap_ci(haz, sel_np, sel_base, np.arange(100), reps=200)
    assert r["power_gap"] == 1.0 and r["excludes_zero"]
