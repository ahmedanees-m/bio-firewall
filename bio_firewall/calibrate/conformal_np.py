"""Optimal-power Neyman-Pearson conformal selection for the escalate / route-to-review
decision.

The layer thresholds a SCALAR risk score and certifies P(escalate | legitimate research) <= alpha with a
Clopper-Pearson bound. Conformal selection (Jin & Candes, "Selection by Prediction with Conformal p-values", JMLR
v24 2023, arXiv:2210.01408) gives the same finite-sample false-selection control via conformal p-values; the
Neyman-Pearson revamp (Qin, Liu, Li, Huang, arXiv:2502.16513, 2025) replaces the raw score with a LIKELIHOOD-RATIO
statistic to MAXIMIZE power at the controlled error rate. For a 1-D monotone score a threshold is already NP-optimal,
so the power only moves when the selector uses the FULL feature vector (per-axis severities + competence band + pLI)
that the scalar collapse discards.

The head-to-head (scalar threshold vs NP likelihood-ratio conformal selection at matched alpha) is OUR
pre-registered experiment - the NP paper neither names Clopper-Pearson nor uses conformal p-values in its rule. We
claim the upgrade only if the NP selector controls the false-escalation rate at alpha AND beats the scalar method on
catch-rate (power) at matched alpha with a CI on the gap excluding 0 (else: keep the certified bound; report the null).

Pure numpy / scikit-learn; no torch. Selector math here (synthetic-testable); the firewall-corpus experiment is
eval/hazard_bench/conformal_np_bench.py.
"""
from __future__ import annotations

import numpy as np


def conformal_pvalues(null_calib: np.ndarray, test_scores: np.ndarray) -> np.ndarray:
    """One-sided conformal p-values (Jin & Candes): under the null (legitimate research), a LARGER score is more
    anomalous. p_j = (1 + #{i in calib : s_i >= s_j}) / (n_calib + 1). Super-uniform under the null, so selecting
    p_j <= alpha controls the marginal false-selection (false-escalation) rate at alpha, finite-sample."""
    null_calib = np.asarray(null_calib, float)
    test_scores = np.asarray(test_scores, float)
    n = len(null_calib)
    ge = (null_calib[None, :] >= test_scores[:, None]).sum(axis=1)        # #{calib_i >= test_j}
    return (1.0 + ge) / (n + 1.0)


def scalar_threshold_select(legit_calib: np.ndarray, test_scores: np.ndarray, alpha: float) -> np.ndarray:
    """The baseline: pick the threshold at the (1-alpha) empirical quantile of the legitimate calibration scores
    (the conformal threshold equivalent for a fixed scalar score), escalate test scores AT/ABOVE it. Controls
    P(escalate | legitimate) <= alpha by construction (same conformal guarantee, scalar score)."""
    legit_calib = np.asarray(legit_calib, float)
    test_scores = np.asarray(test_scores, float)
    # conformal threshold: the smallest t with #{calib >= t}/(n+1) <= alpha  ==  ceil((1-alpha)(n+1))-th order stat
    k = int(np.ceil((1.0 - alpha) * (len(legit_calib) + 1))) - 1
    k = min(max(k, 0), len(legit_calib) - 1)
    tau = np.sort(legit_calib)[k]
    return test_scores >= tau


def np_lr_select(Xtr: np.ndarray, ytr: np.ndarray, Xcalib_null: np.ndarray, Xtest: np.ndarray,
                 alpha: float, seed: int = 1234) -> dict:
    """Neyman-Pearson conformal selection. Fit a likelihood-ratio statistic (calibrated logistic regression: the
    log-odds is a monotone transform of f1/f0, the NP-optimal statistic) on a TRAIN split; score the legitimate-null
    calibration + the test set; convert to conformal p-values against the null; escalate p <= alpha.
    Returns {selected (bool mask over test), lr_test, pvalues}."""
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed).fit(Xtr, ytr)

    def lr(X):
        return clf.decision_function(np.asarray(X, float))                # log f1/f0 (monotone in the LR)

    lr_null = lr(Xcalib_null)
    lr_test = lr(Xtest)
    p = conformal_pvalues(lr_null, lr_test)
    return {"selected": p <= alpha, "lr_test": lr_test, "pvalues": p, "lr_null": lr_null}


def catch_rate(selected: np.ndarray, hazard: np.ndarray) -> float:
    """Power = fraction of independently-hazardous test plans escalated."""
    selected, hazard = np.asarray(selected, bool), np.asarray(hazard, int)
    nh = max(1, int((hazard == 1).sum()))
    return float((selected & (hazard == 1)).sum() / nh)


def false_select_rate(selected: np.ndarray, hazard: np.ndarray) -> float:
    """Realized false-escalation rate among legitimate (non-hazard) test plans."""
    selected, hazard = np.asarray(selected, bool), np.asarray(hazard, int)
    nb = max(1, int((hazard == 0).sum()))
    return float((selected & (hazard == 0)).sum() / nb)


def power_gap_ci(hazard: np.ndarray, sel_np: np.ndarray, sel_base: np.ndarray, groups: np.ndarray,
                 reps: int = 2000, seed: int = 1234) -> dict:
    """Group-clustered bootstrap CI on the power gap (catch_rate_NP - catch_rate_baseline). Resample GROUPS (gene
    clusters) so the CI is not inflated by within-gene correlation."""
    hazard = np.asarray(hazard, int)
    groups = np.asarray(groups)
    uniq = np.unique(groups)
    idx_by_g = {g: np.where(groups == g)[0] for g in uniq}
    rng = np.random.RandomState(seed)
    base_gap = catch_rate(sel_np, hazard) - catch_rate(sel_base, hazard)
    gaps = []
    for _ in range(reps):
        gs = uniq[rng.randint(0, len(uniq), len(uniq))]
        idx = np.concatenate([idx_by_g[g] for g in gs])
        gaps.append(catch_rate(sel_np[idx], hazard[idx]) - catch_rate(sel_base[idx], hazard[idx]))
    lo, hi = np.percentile(gaps, [2.5, 97.5])
    return {"power_gap": round(float(base_gap), 4), "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "excludes_zero": bool(lo > 0.0)}
