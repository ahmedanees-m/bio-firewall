"""Distribution-free, finite-sample calibration for the screen: a certified false-refuse ceiling plus a
competence-conditioned confidence. Three pieces:

  1. NEYMAN-PEARSON FALSE-REFUSE CERTIFICATE. The firewall refuses only on unambiguous hard rules, so its
     empirical false-refuse on legitimate research is near zero; this is turned into a certificate: a
     Clopper-Pearson (1-delta) UPPER bound on P(refuse | legitimate research) <= alpha, reported as a
     nominal-vs-empirical coverage curve.

  2. COMPETENCE-CONDITIONED CONFIDENCE. Confidence is conditioned on KB-COVERAGE: a clean allow is high-confidence
     only when the gene is IN the firewall's data (there is evidence it is benign); an OUT-of-coverage allow is LOW
     confidence (the competence boundary, where the misses live) and is a candidate for abstention. This routes the
     unknown to 'low' rather than manufacturing a signal that is not there, and the tiers are monotone by construction.

  3. SELECTIVE-ABSTENTION operating curve. A continuous risk score (axis severity + a continuous gnomAD pLI nudge
     inside the clear band, so constrained off-list genes rank above random benigns) drives a threshold sweep: each
     operating point trades auto-allow MISS-rate against ESCALATION-rate, giving the achievable Pareto frontier.

Pure numpy/scipy, no torch/esm. Pre-registered gate: prereg/ws_biofirewall.yaml::upgrade_v04_v10.conformal.
"""
from __future__ import annotations

from bio_firewall.data import dosage, gene_roles
from bio_firewall.hazard.finding import SEVERITY

_DETERMINISTIC = {
    "cargo.select_agent_or_toxin", "cargo.gene_drive", "germline.human_heritable_clinical",
    "germline.human_embryo_research", "edit.oncogenic_fusion_by_design", "locus.oncogene_activation_by_design",
}
# strong-positive locus evidence (named clinical-CIS / explicit cancer role) vs weak mechanism flags (dosage only)
_STRONG_LOCUS = {"locus.genotoxic_proximity", "locus.tumor_suppressor_disruption", "locus.oncogene_proximity"}


# --------------------------------------------------------------------------------------------------------------
# competence boundary + risk score
# --------------------------------------------------------------------------------------------------------------
def kb_coverage(gene: str) -> str:
    """Is the firewall COMPETENT to clear this gene? 'in' = a hazard role is known (CancerMine/DepMap);
    'constraint' = no hazard role but gnomAD constraint is known (a characterized gene); 'out' = absent from all
    vendored data (the competence boundary - a clean allow here is epistemically a guess)."""
    if gene_roles(gene):
        return "in"
    if dosage(gene) is not None:
        return "constraint"
    return "out"


def _worst(verdict: dict):
    triggered = [f for f in verdict.get("axes", {}).values() if f["decision"] != "clear"]
    return max(triggered, key=lambda f: SEVERITY[f["decision"]]) if triggered else None


def risk_score(verdict: dict, gene: str = "") -> float:
    """Continuous hazard score in [0,1]: a severity band + a continuous gnomAD-pLI nudge inside the CLEAR band, so
    a constrained (often cancer-relevant) off-list gene ranks above a random benign one - enabling selective
    escalation that recovers misses at a lower false-flag cost than blanket escalation."""
    w = _worst(verdict)
    if w is None:                                   # clear -> within-band continuous signal from constraint
        dz = dosage(gene)
        pli = dz[0] if dz else 0.0
        return round(0.29 * float(pli), 4)
    band = {3: 0.90, 2: 0.60, 1: 0.30}[SEVERITY[w["decision"]]]
    strong = 0.09 if (w.get("rule_id") in _DETERMINISTIC or w.get("rule_id") in _STRONG_LOCUS) else 0.0
    return round(band + strong, 4)


def calibrated_confidence(verdict: dict, gene: str = "") -> str:
    """Competence-conditioned confidence (monotone by construction):
      high     : a deterministic hard rule fired, OR a strong-positive locus flag (named clinical-CIS / role)
      moderate : a weak mechanism flag (dosage-only), OR a clean allow of an IN-CONSTRAINT-DATA gene
      low      : a clean allow of an OUT-of-coverage gene (the competence boundary - the misses live here)."""
    w = _worst(verdict)
    if w is not None:
        if w.get("rule_id") in _DETERMINISTIC:
            return "high"
        if w.get("rule_id") in _STRONG_LOCUS:
            return "high"
        return "moderate"                            # dosage-sensitive / weaker mechanism flag
    return "moderate" if kb_coverage(gene) != "out" else "low"   # clean allow -> condition on coverage


# --------------------------------------------------------------------------------------------------------------
# 1. Neyman-Pearson false-refuse certificate (Clopper-Pearson upper bound)
# --------------------------------------------------------------------------------------------------------------
def clopper_pearson_upper(k: int, n: int, conf: float = 0.95) -> float:
    """One-sided (1-conf rejected) upper confidence bound on a binomial rate from k events in n trials."""
    if n == 0:
        return 1.0
    if k == 0:
        return float(1.0 - (1.0 - conf) ** (1.0 / n))
    from scipy.stats import beta
    return float(beta.ppf(conf, k + 1, n - k))


TOLERANCE = 0.02   # the pre-registered slack; kept unchanged so frozen results stay comparable


def false_refuse_certificate(n_legit: int, n_refused: int, alphas=(0.01, 0.05, 0.10),
                             conf: float = 0.95, tolerance: float = TOLERANCE) -> dict:
    """Bound P(refuse | legitimate research) on the evaluated corpus.

    Empirical rate plus a one-sided Clopper-Pearson UPPER bound at `conf`.

    The nominal target and the tolerated threshold are reported SEPARATELY, because they are not
    the same criterion and conflating them overstates what was met. With the pre-registered
    tolerance of 0.02, an upper bound of 0.0103 meets the tolerated threshold at alpha = 0.01
    (0.0103 <= 0.03) but NOT the nominal 1% ceiling (0.0103 > 0.01). `meets_nominal` and
    `meets_tolerated` say which is which; `pass` is retained as a backward-compatible alias of
    `meets_tolerated` so previously frozen results remain readable, and should not be read as
    the nominal ceiling having been met.

    This bounds over-refusal on the corpus supplied. It is not a deployment guarantee: it
    inherits whatever sampling and exchangeability properties that corpus has.
    """
    emp = (n_refused / n_legit) if n_legit else 1.0
    ub = clopper_pearson_upper(n_refused, n_legit, conf)
    curve = []
    for a in alphas:
        meets_nominal = bool(ub <= a)
        meets_tolerated = bool(ub <= a + tolerance)
        curve.append({"alpha_nominal": a, "tolerance": tolerance,
                      "alpha_tolerated": round(a + tolerance, 4),
                      "empirical_false_refuse": round(emp, 4),
                      "certified_upper_bound": round(ub, 4),
                      "meets_nominal": meets_nominal, "meets_tolerated": meets_tolerated,
                      "alpha": a, "pass": meets_tolerated})
    return {"n_legit": n_legit, "n_refused": n_refused, "empirical_false_refuse": round(emp, 4),
            "confidence": conf, "tolerance": tolerance,
            "certified_upper_bound": round(ub, 4), "coverage_curve": curve,
            "all_meet_nominal": all(c["meets_nominal"] for c in curve),
            "all_meet_tolerated": all(c["meets_tolerated"] for c in curve),
            "all_pass": all(c["meets_tolerated"] for c in curve),
            "criterion": ("certified upper bound <= alpha + tolerance; see meets_nominal for the "
                          "unrelaxed alpha. 'pass'/'all_pass' alias the TOLERATED criterion.")}


# --------------------------------------------------------------------------------------------------------------
# 2. Mondrian (per-decision-class) reliability + monotonicity of the calibrated confidence
# --------------------------------------------------------------------------------------------------------------
def _boot_ci(flags, reps=2000, seed=7):
    """Percentile bootstrap, except on a constant sample.

    A percentile bootstrap over an all-correct subgroup resamples only ones and returns [1, 1],
    which is an artefact of the method rather than evidence that future error is zero. For a
    constant sample we report an exact Clopper-Pearson interval instead, which keeps the
    uncertainty that the sample size actually leaves.
    """
    import numpy as np
    if not flags:
        return [0.0, 0.0]
    a = np.asarray(flags)
    n, k = len(a), int(a.sum())
    if a.min() == a.max():
        from scipy.stats import beta
        lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
        hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
        return [round(lo, 3), round(hi, 3)]
    rng = np.random.RandomState(seed)
    m = [a[rng.randint(0, n, n)].mean() for _ in range(reps)]
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def mondrian_reliability(rows: list[dict]) -> dict:
    """rows carry: decision, correct (bool vs independent label). Per-decision-class empirical correctness (the
    Mondrian conditioning): a per-class reliability."""
    by: dict[str, list[int]] = {}
    for r in rows:
        by.setdefault(r["decision"], []).append(int(r["correct"]))
    return {d: {"n": len(v), "reliability": round(sum(v) / len(v), 3), "ci95": _boot_ci(v)} for d, v in by.items()}


def confidence_monotonicity(rows: list[dict]) -> dict:
    """rows carry: conf in {high,moderate,low}, correct (bool). The confidence tiers are calibrated iff empirical
    accuracy is monotone high >= moderate >= low."""
    acc = {}
    for t in ("high", "moderate", "low"):
        v = [int(r["correct"]) for r in rows if r["conf"] == t]
        acc[t] = {"n": len(v), "accuracy": round(sum(v) / len(v), 3) if v else None, "ci95": _boot_ci(v)}
    seq = [acc[t]["accuracy"] for t in ("high", "moderate", "low") if acc[t]["accuracy"] is not None]
    monotone = all(seq[i] >= seq[i + 1] - 1e-9 for i in range(len(seq) - 1))
    return {"tier_accuracy": acc, "monotone_high_ge_moderate_ge_low": monotone}


# --------------------------------------------------------------------------------------------------------------
# 3. Selective-abstention operating curve (the achievable Pareto frontier)
# --------------------------------------------------------------------------------------------------------------
def selective_curve(risks, hazard, n_steps: int = 41) -> list[dict]:
    """risks: continuous risk per plan; hazard: 1 if independently hazardous else 0. Sweep an abstain threshold
    tau: plans with risk < tau are AUTO-ALLOWED, the rest ESCALATED. Each point = (tau, auto_allow_coverage,
    miss_rate among hazards auto-allowed, escalation_rate among benigns)."""
    import numpy as np
    risks = np.asarray(risks, float)
    hazard = np.asarray(hazard, int)
    benign = hazard == 0
    nh, nb = max(1, hazard.sum()), max(1, benign.sum())
    out = []
    for tau in np.linspace(0.0, float(risks.max()) + 1e-6, n_steps):
        auto = risks < tau
        miss = int((auto & (hazard == 1)).sum()) / nh                 # hazards we auto-cleared (the safety cost)
        esc_benign = int((~auto & benign).sum()) / nb                 # benigns we escalated (the usability cost)
        out.append({"tau": round(float(tau), 3), "auto_allow_frac": round(float(auto.mean()), 3),
                    "miss_rate": round(miss, 4), "benign_escalation_rate": round(esc_benign, 4)})
    return out
