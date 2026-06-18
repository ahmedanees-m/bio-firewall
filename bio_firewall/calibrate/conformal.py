"""WS-CONFORMAL (v0.4.0) — replace the WITHDRAWN 'determinism' headline with the operational moat an LLM cannot
offer: a CALIBRATED, certified ceiling on over-action, plus a competence-conditioned confidence that fixes the P8
inversion. Three pieces, all distribution-free / finite-sample honest:

  1. NEYMAN-PEARSON FALSE-REFUSE CERTIFICATE. The deployment moat (head-to-head claim D: open LLM judges flip
     refuse->allow 50-83% under injection AND a frontier LLM over-refuses legitimate research 40%). The firewall
     refuses ONLY on unambiguous hard rules, so its empirical false-refuse on legitimate research is ~0 — we turn
     that into a CERTIFICATE: a Clopper-Pearson (1-delta) UPPER bound on P(refuse | legitimate research) <= alpha,
     reported as a nominal-vs-empirical coverage curve. (This is exactly what an LLM judge cannot promise.)

  2. COMPETENCE-CONDITIONED CONFIDENCE (fixes the P8 inversion). The v0.3 tiers were inverted (high 0.789 <
     moderate 0.938) because a CLEAN ALLOW was labelled 'high' regardless of whether the gene was inside the
     firewall's knowledge base — so its confident MISSES (independently-hazardous genes ABSENT from its data) sat
     in the 'high' tier. The fix conditions confidence on KB-COVERAGE: a clean allow is high-confidence only when
     the gene is IN the firewall's data (we have evidence it is benign); an OUT-of-coverage allow is LOW confidence
     (the competence boundary, where the misses live) and is a candidate for abstention. This does NOT manufacture
     a signal that is not there — it HONESTLY routes the unknown to 'low'.

  3. SELECTIVE-ABSTENTION operating curve. A continuous risk score (axis severity + continuous gnomAD pLI for the
     clear band, so constrained off-list genes rank above random benigns) drives a threshold sweep: each operating
     point trades auto-allow MISS-rate against ESCALATION-rate. The honest deliverable is the achievable Pareto
     frontier (the pre-committed honest-failure path: report operating points, the guarantee is the contribution).

Pure numpy/scipy — no torch/esm. Pre-registered gate: prereg/ws_biofirewall.yaml::upgrade_v04_v10.conformal.
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
    vendored data (the competence boundary — a clean allow here is epistemically a guess)."""
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
    a constrained (often cancer-relevant) off-list gene ranks above a random benign one — enabling selective
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
    """Competence-conditioned confidence (monotone by construction, fixes the inversion):
      high     : a deterministic hard rule fired, OR a strong-positive locus flag (named clinical-CIS / role)
      moderate : a weak mechanism flag (dosage-only), OR a clean allow of an IN-CONSTRAINT-DATA gene
      low      : a clean allow of an OUT-of-coverage gene (the competence boundary — the misses live here)."""
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


def false_refuse_certificate(n_legit: int, n_refused: int, alphas=(0.01, 0.05, 0.10), conf: float = 0.95) -> dict:
    """Certify P(refuse | legitimate research) <= alpha. Empirical rate + a (1-conf) Clopper-Pearson UPPER bound;
    per-alpha pass iff the UPPER bound <= alpha + 0.02 (the pre-registered tolerance). The coverage curve is the
    nominal alpha vs the (empirical, certified-upper) pair."""
    emp = (n_refused / n_legit) if n_legit else 1.0
    ub = clopper_pearson_upper(n_refused, n_legit, conf)
    curve = [{"alpha": a, "empirical_false_refuse": round(emp, 4),
              "certified_upper_bound": round(ub, 4), "pass": ub <= a + 0.02} for a in alphas]
    return {"n_legit": n_legit, "n_refused": n_refused, "empirical_false_refuse": round(emp, 4),
            "confidence": conf, "certified_upper_bound": round(ub, 4),
            "coverage_curve": curve, "all_pass": all(c["pass"] for c in curve)}


# --------------------------------------------------------------------------------------------------------------
# 2. Mondrian (per-decision-class) reliability + monotonicity of the calibrated confidence
# --------------------------------------------------------------------------------------------------------------
def _boot_ci(flags, reps=2000, seed=7):
    import numpy as np
    if not flags:
        return [0.0, 0.0]
    rng = np.random.RandomState(seed)
    a = np.asarray(flags)
    m = [a[rng.randint(0, len(a), len(a))].mean() for _ in range(reps)]
    return [round(float(np.percentile(m, 2.5)), 3), round(float(np.percentile(m, 97.5)), 3)]


def mondrian_reliability(rows: list[dict]) -> dict:
    """rows carry: decision, correct (bool vs independent label). Per-decision-class empirical correctness (the
    Mondrian conditioning) — REPLACES the inverted 3-tier table with an honest per-class reliability."""
    by: dict[str, list[int]] = {}
    for r in rows:
        by.setdefault(r["decision"], []).append(int(r["correct"]))
    return {d: {"n": len(v), "reliability": round(sum(v) / len(v), 3), "ci95": _boot_ci(v)} for d, v in by.items()}


def confidence_monotonicity(rows: list[dict]) -> dict:
    """rows carry: conf in {high,moderate,low}, correct (bool). The P8-inversion fix is VALIDATED iff empirical
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
