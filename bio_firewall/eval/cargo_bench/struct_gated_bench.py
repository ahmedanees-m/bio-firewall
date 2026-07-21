"""Close the struct negative at the operating point. The mean ensemble diluted ESM at 1%-FPR
(incremental TPR -0.48) because it averaged in a weak, low-confidence fold channel everywhere. The fix: a
CONFIDENCE-GATED fusion, using the structure signal only where the predicted-structure
mean pLDDT is high, else defer to ESM. Reuses the frozen Benchmark-2 ESM vectors + the Foldseek structural score per
held-out accession (AlphaFold-DB v6, no GPU) + a mean-pLDDT per accession parsed from the cached AF-DB .cif files.

Pre-registered gate (prereg upgrade_v08_completeness.struct_gated): NON-NEGATIVE incremental TPR@1%FPR over ESM-alone
on the full <=40%-id holdout (no longer dilutes) AND STRICTLY POSITIVE incremental TPR@1%FPR on the high-confidence
-structure subset (CI). Fallback (pre-committed): if even gated fusion does not add at 1%-FPR -> report the structure
channel as a ranking-level (AUROC) corroborator only (its documented value).

Reproduce on the VM (artifacts in ~/bf_b2, ~/bf_struct):
    BF_B2_DIR=~/bf_b2 BF_STRUCT_SCORES=~/bf_struct/struct_scores.json BF_PLDDT=~/bf_struct/plddt.json \
      python -c "from bio_firewall.eval.cargo_bench import struct_gated_bench as s; import json; print(json.dumps(s.run()['gate'], indent=2))"
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from bio_firewall.eval.cargo_bench.decorr import load_aligned, paired_boot_diff, tpr_at_fpr
from bio_firewall.hazard.struct_channel import abstain_mask, confidence_gated_score, ensemble_score


def run(out_dir: str = "bf_struct_gated", bf_b2: str | None = None, struct_scores: str | None = None,
        plddt_scores: str | None = None, plddt_min: float = 70.0) -> dict:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    bf_b2 = Path(bf_b2 or os.environ.get("BF_B2_DIR", "bf_b2")).expanduser()
    wd = Path(out_dir)
    wd.mkdir(parents=True, exist_ok=True)
    scores = json.loads(Path(struct_scores or os.environ.get("BF_STRUCT_SCORES", "")).expanduser().read_text())
    plddt_map = json.loads(Path(plddt_scores or os.environ.get("BF_PLDDT", "")).expanduser().read_text())

    d = load_aligned(bf_b2)
    Xtr, ytr, Xte, yte, test_k, cte = d["Xtr"], d["ytr"], d["Xte"], d["yte"], d["test_k"], np.asarray(d["cte"])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Xtr, ytr)
    p_esm = clf.predict_proba(Xte)[:, 1]
    struct = np.array([float(scores.get(k, 0.0)) for k in test_k])
    plddt = np.array([float(plddt_map.get(k, 0.0)) for k in test_k])
    hi = plddt >= plddt_min

    gated = confidence_gated_score(p_esm, struct, plddt, plddt_min)
    mean_ens = ensemble_score(p_esm, struct)                          # the mean ensemble (for contrast)

    def block(p, y=yte):
        return {"TPR@1%FPR": round(tpr_at_fpr(y, p), 3),
                "AUROC": round(float(roc_auc_score(y, p)), 3) if len(set(y)) > 1 else 0.5}

    incr_gated = paired_boot_diff(yte, gated, p_esm, cte, tpr_at_fpr)         # gated - ESM, full holdout
    incr_mean = paired_boot_diff(yte, mean_ens, p_esm, cte, tpr_at_fpr)       # mean - ESM (the failure)

    # high-confidence-structure subset: where the fold channel is trusted, does structure ADD over ESM?
    sub = {"n": int(hi.sum()), "n_pos": int(yte[hi].sum()), "n_neg": int((yte[hi] == 0).sum())}
    if hi.sum() >= 10 and 0 < yte[hi].sum() < hi.sum():
        gated_hi = 0.5 * (np.asarray(_n01(p_esm))[hi] + np.asarray(_n01(struct))[hi])    # ensemble on the subset
        esm_hi = np.asarray(_n01(p_esm))[hi]
        incr_hi = paired_boot_diff(yte[hi], gated_hi, esm_hi, cte[hi], tpr_at_fpr)
        sub.update({"esm_alone": block(esm_hi, yte[hi]), "esm_plus_structure": block(gated_hi, yte[hi]),
                    "incremental_TPR@1%FPR": incr_hi})
    else:
        incr_hi = None
        sub["note"] = "high-confidence subset too small / single-class for a 1%-FPR estimate"

    full_non_negative = bool(incr_gated["ci95"][0] >= -1e-9 or incr_gated["median"] >= 0.0)
    subset_positive = bool(incr_hi is not None and incr_hi["ci95"][0] > 0.0)
    gate_pass = bool(full_non_negative and subset_positive)

    res = {
        "n_test": int(len(yte)), "n_struct_covered": int((struct != 0).sum()),
        "n_high_confidence": int(hi.sum()), "plddt_min": plddt_min,
        "esm_alone": block(p_esm), "structure_alone": block(struct),
        "gated_fusion": block(gated), "v06_mean_ensemble": block(mean_ens),
        "incremental_TPR_full_gated_minus_esm": incr_gated,
        "incremental_TPR_full_v06_mean_minus_esm": incr_mean,
        "high_confidence_subset": sub,
        "abstain_on_disagreement": {"n": int(abstain_mask(p_esm, struct).sum())},
        "gate": {
            "criterion": "non-negative incremental TPR@1%FPR over ESM on the full holdout AND strictly positive on "
                         "the high-confidence-structure subset (CI)",
            "full_non_negative": full_non_negative, "subset_positive": subset_positive, "pass": gate_pass,
            "fallback_if_fail": "report the structure channel as a ranking-level (AUROC) corroborator only "
                                "(composition-free AUROC ~0.88), no operating-point lift claim.",
        },
        "seed": 1234,
    }
    (wd / "results.json").write_text(json.dumps(res, indent=2))
    return res


def _n01(xs):
    from bio_firewall.hazard.struct_channel import normalize01
    return normalize01(xs)
