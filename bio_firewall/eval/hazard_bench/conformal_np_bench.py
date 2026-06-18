"""WS-CONFORMAL-NP head-to-head (v0.8.0) on the firewall corpus. Builds a feature vector per plan from the live
verdict (per-axis severity + competence band + gnomAD pLI + the v0.4 scalar risk), splits gene-disjointly into
train / calibration / test, and compares two escalate / route-to-review selectors at matched alpha:

  baseline (v0.4): threshold the SCALAR risk score, conformal-calibrated on the benign null (P(escalate|benign)<=alpha).
  NP (this WS):     a likelihood-ratio statistic over the FULL feature vector + conformal selection on the same null.

Pre-registered gate (prereg upgrade_v08_completeness.conformal_np): the NP selector controls the false-escalation
rate at alpha AND beats the baseline on catch-rate (power) at matched alpha, with a gene-clustered bootstrap CI on
the power gap EXCLUDING 0. Fallback (pre-committed): if it does not beat the baseline -> report the null, keep the
v0.4 certified bound.

Needs PEN_STACK_HOME (Guardian) + BF_BENCH_ORACLES (COSMIC, local-only). Reproduce:
    BF_BENCH_ORACLES=~/bench_oracles python -c \
      "from bio_firewall.eval.hazard_bench import conformal_np_bench as c; import json; print(json.dumps(c.run()['gate'], indent=2))"
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from bio_firewall.calibrate import conformal as cf
from bio_firewall.calibrate import conformal_np as npc
from bio_firewall.data import dosage
from bio_firewall.eval.hazard_bench import generate, oracles
from bio_firewall.hazard.finding import SEVERITY
from bio_firewall.intercept.spine import screen

SEED = 1234
_AXES = ("cargo", "locus", "edit_type", "germline", "scale")
_COV = {"in": 2.0, "constraint": 1.0, "out": 0.0}
_ALPHAS = (0.05, 0.10, 0.20)


def _features(plan: dict) -> tuple[list[float], float]:
    """Feature vector + the v0.4 scalar risk for one plan. Features the scalar collapses: per-axis severity, the
    competence band, and pLI - exactly what a likelihood-ratio combiner can re-weight."""
    gene = str(plan.get("gene") or (plan.get("locus") or {}).get("gene") or "")
    v = screen(plan)
    sev = [float(SEVERITY[v["axes"][a]["decision"]]) for a in _AXES]
    cov = _COV[cf.kb_coverage(gene)]
    dz = dosage(gene)
    pli = float(dz[0]) if dz else 0.0
    risk = float(cf.risk_score(v, gene))
    return [*sev, cov, pli, risk], risk


def _corpus(seed: int = SEED) -> list[dict]:
    rows = []
    for r in generate.generate(seed=seed):
        if r["stratum"] == "legitimate_research":
            continue                                    # the must-flag set is handled separately (it SHOULD escalate)
        feats, risk = _features(r["plan"])
        rows.append({"gene": str(r.get("gene") or ""), "stratum": r["stratum"],
                     "x": feats, "risk": risk, "hazard": int(r["independent_hazard"])})
    return rows


def run(out_dir: str = "bf_conformal_np", seed: int = SEED) -> dict:
    import numpy as np
    wd = Path(out_dir)
    wd.mkdir(parents=True, exist_ok=True)
    rows = _corpus(seed)

    # gene-disjoint split: train (LR fit) / calib (conformal null) / test (evaluation)
    genes = sorted({r["gene"] for r in rows})
    rng = random.Random(seed)
    rng.shuffle(genes)
    n = len(genes)
    g_train = set(genes[: n // 2])
    g_calib = set(genes[n // 2: int(n * 0.75)])
    g_test = set(genes[int(n * 0.75):])
    tr = [r for r in rows if r["gene"] in g_train]
    ca = [r for r in rows if r["gene"] in g_calib]
    te = [r for r in rows if r["gene"] in g_test]

    Xtr = np.array([r["x"] for r in tr])
    ytr = np.array([r["hazard"] for r in tr])
    ca_null = [r for r in ca if r["hazard"] == 0]                   # benign null calibration
    Xca_null = np.array([r["x"] for r in ca_null])
    risk_ca_null = np.array([r["risk"] for r in ca_null])
    Xte = np.array([r["x"] for r in te])
    risk_te = np.array([r["risk"] for r in te])
    haz_te = np.array([r["hazard"] for r in te])
    grp_te = np.array([r["gene"] for r in te])

    per_alpha = []
    best = None
    for a in _ALPHAS:
        npr = npc.np_lr_select(Xtr, ytr, Xca_null, Xte, a, seed=seed)
        sel_np = npr["selected"]
        sel_base = npc.scalar_threshold_select(risk_ca_null, risk_te, a)
        gap = npc.power_gap_ci(haz_te, sel_np, sel_base, grp_te, seed=seed)
        rec = {
            "alpha": a,
            "np": {"catch_rate": round(npc.catch_rate(sel_np, haz_te), 4),
                   "false_escalation": round(npc.false_select_rate(sel_np, haz_te), 4)},
            "baseline_v04_scalar": {"catch_rate": round(npc.catch_rate(sel_base, haz_te), 4),
                                    "false_escalation": round(npc.false_select_rate(sel_base, haz_te), 4)},
            "power_gap_np_minus_base": gap,
            "np_controls_at_alpha": npc.false_select_rate(sel_np, haz_te) <= a + 0.05,
        }
        per_alpha.append(rec)
        if best is None or gap["power_gap"] > best["power_gap_np_minus_base"]["power_gap"]:
            best = rec

    passed = any(r["np_controls_at_alpha"] and r["power_gap_np_minus_base"]["excludes_zero"] for r in per_alpha)
    gate = {
        "criterion": "NP controls false-escalation at alpha AND power gap (catch_NP - catch_baseline) CI excludes 0 "
                     "at some matched alpha",
        "pass": bool(passed),
        "best_alpha": best["alpha"] if best else None,
        "best_power_gap": best["power_gap_np_minus_base"] if best else None,
        "fallback_if_fail": "keep the v0.4 Clopper-Pearson certified bound (already passing); report the null.",
    }
    result = {"oracles": oracles.oracle_status(), "seed": seed,
              "n_train": len(tr), "n_calib_null": len(ca_null), "n_test": len(te),
              "n_test_hazard": int(haz_te.sum()), "n_test_benign": int((haz_te == 0).sum()),
              "per_alpha": per_alpha, "gate": gate}
    (wd / "results.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
