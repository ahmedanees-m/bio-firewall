"""Benchmark 4 — calibration, the HONEST (not conformal) version. No outcome labels exist, so we measure against
Benchmark-1's INDEPENDENT hazard labels:
  - tier validity      : do high-confidence (deterministic) verdicts agree with the independent label more than
                         moderate (mechanism) than low (ML)?
  - risk-coverage      : as we escalate lower-confidence verdicts to review (shrinking the auto-handled set),
                         does the residual error on the auto-handled set drop?
  - abstention utility : hazard-miss rate of the high-confidence auto-allow set vs the overall allow set."""
from __future__ import annotations

from bio_firewall.eval.hazard_bench.score import intercepted

_RANK = {"high": 2, "moderate": 1, "low": 0}


def _correct(row: dict) -> bool:
    """A verdict is correct vs the independent label iff it intercepts a hazard and allows a benign gene."""
    if row["independent_hazard"]:
        return intercepted(row["fw"])
    return row["fw"] == "allow"


def run_calibration(rows: list[dict]) -> dict:
    # consider only the labeled locus universe (hazard + clean negatives); skip the policy/legit strata
    use = [r for r in rows if r["stratum"] in (
        "tier1_gold", "cosmic_overlap", "cosmic_generalization", "negative_benign", "negative_safe_harbour")]
    for r in use:
        r["_correct"] = _correct(r)
        r["_conf"] = r.get("conf", "high")

    # ---- tier validity ----
    tiers: dict[str, list[int]] = {}
    for r in use:
        tiers.setdefault(r["_conf"], []).append(int(r["_correct"]))
    tier_acc = {t: {"n": len(v), "accuracy": round(sum(v) / len(v), 3)} for t, v in tiers.items()}

    # ---- risk-coverage (selective prediction) at confidence thresholds high / high+moderate / all ----
    curve = []
    for thr_name, keep_ranks in [("high_only", {2}), ("high+moderate", {2, 1}), ("all", {2, 1, 0})]:
        kept = [r for r in use if _RANK.get(r["_conf"], 0) in keep_ranks]
        if not kept:
            continue
        err = sum(1 for r in kept if not r["_correct"]) / len(kept)
        curve.append({"threshold": thr_name, "coverage": round(len(kept) / len(use), 3),
                      "error_on_kept": round(err, 3)})

    # ---- abstention usefulness: hazard-miss rate of high-confidence allow vs ALL allow ----
    haz = [r for r in use if r["independent_hazard"]]
    allow_all = [r for r in haz if r["fw"] == "allow"]
    allow_highconf = [r for r in haz if r["fw"] == "allow" and r["_conf"] == "high" and not r.get("abstain")]
    miss_all = len(allow_all) / len(haz) if haz else 0.0
    miss_high = len(allow_highconf) / len(haz) if haz else 0.0

    return {
        "n": len(use),
        "tier_validity": tier_acc,
        "tier_order_high_ge_moderate_ge_low": _ordered(tier_acc),
        "risk_coverage_curve": curve,
        "risk_coverage_monotone": _monotone([c["error_on_kept"] for c in curve]),
        "abstention": {
            "hazard_miss_rate_all_allow": round(miss_all, 3),
            "hazard_miss_rate_highconf_allow": round(miss_high, 3),
            "note": "if the firewall's misses are CONFIDENT (high-conf allows of genes absent from its data), "
                    "abstention cannot rescue them — an honest limit of data-membership calibration.",
        },
    }


def _ordered(tier_acc: dict) -> bool:
    seq = [tier_acc[t]["accuracy"] for t in ("high", "moderate", "low") if t in tier_acc]
    return all(seq[i] >= seq[i + 1] for i in range(len(seq) - 1))


def _monotone(xs: list[float]) -> bool:
    return all(xs[i] <= xs[i + 1] for i in range(len(xs) - 1))
