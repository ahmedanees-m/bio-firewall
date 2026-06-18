"""WS-LOCUS-OUTCOME (v0.5.0) — outcome-validate the locus axis on REAL integration-site data, the open-data floor.

§6 limit #2: the locus genotoxicity proxy flags on MECHANISM and is NOT outcome-validated; the two gene-census
benchmarks (COSMIC 80.4%, OncoKB 82.0%) are recall-against-curation, not validation-against-outcomes. This module
tests whether the firewall's locus-risk ENRICHES for an integration-site OUTCOME signal in real data.

Open-data floor: **VISDB** (Viral Integration Site DataBase, Tang et al. 2020, NAR 10.1093/nar/gkz867) — the same
catalogue PEN-STACK's v5.2 genotoxicity oracle uses (local-only on the VM; never committed). Each integration site
carries a **Sample type** (Tumor vs non-tumor); we map each site to its nearest gene (GENCODE coords) and test
whether firewall-flagged loci are enriched among TUMOR-associated integration sites.

PRE-REGISTERED gate (prereg upgrade_v04_v10.locus_outcome): OR with CI excluding 1, OR AUROC with CI excluding 0.5.
HONEST status (pre-committed, user deferred controlled-access dbGaP/EGA 2026-06-18): this VISDB floor is an
ASSOCIATIVE, RETROSPECTIVE enrichment — 'tumor sample-source' is not a causal insertional-oncogenesis outcome and
is confounded by virus biology (HTLV→ATL, HIV in cancer patients). A modest validated enrichment is the floor; the
CAUSAL / prospective clonal-outcome validation remains 'outcome-validation pending — data access in review'.

Harness (`validate_enrichment`) is generic + torch-free (numpy/sklearn); the VISDB run (`run_visdb`) needs pandas +
the local VISDB + gene_coords (VM only).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

SEED = 1234
WINDOW_BP = 50_000


# --------------------------------------------------------------------------------------------------------------
# generic enrichment harness (gene-clustered bootstrap — a gene appears at many sites; cluster to avoid pseudo-rep)
# --------------------------------------------------------------------------------------------------------------
def _auroc(y, p, w=None):
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y, p, sample_weight=w)) if len(set(y.tolist() if hasattr(y, "tolist") else y)) > 1 else 0.5


def _odds_ratio(flag, outcome, w=None):
    import numpy as np
    flag, outcome = np.asarray(flag, int), np.asarray(outcome, int)
    w = np.ones(len(flag)) if w is None else np.asarray(w, float)
    a = w[(flag == 1) & (outcome == 1)].sum() + 0.5          # Haldane–Anscombe correction
    b = w[(flag == 1) & (outcome == 0)].sum() + 0.5
    c = w[(flag == 0) & (outcome == 1)].sum() + 0.5
    d = w[(flag == 0) & (outcome == 0)].sum() + 0.5
    return float((a * d) / (b * c))


def _cluster_boot(metric, clusters, reps=800, seed=SEED):
    """Gene-clustered bootstrap via a SAMPLE-WEIGHT resample (no per-rep concatenation): draw cluster multiplicities
    from a multinomial over genes, broadcast to per-row weights, and call the (weighted) metric once per rep."""
    import numpy as np
    clusters = np.asarray(clusters)
    uc, inv = np.unique(clusters, return_inverse=True)       # inv = cluster index per row
    rng = np.random.RandomState(seed)
    vals = []
    for _ in range(reps):
        counts = rng.multinomial(len(uc), np.full(len(uc), 1.0 / len(uc)))   # resample genes with replacement
        w = counts[inv].astype(float)
        try:
            vals.append(metric(w))
        except Exception:  # noqa: BLE001 - degenerate resample (one class) -> skip
            continue
    v = np.array(sorted(x for x in vals if x == x))
    return [round(float(np.percentile(v, 2.5)), 4), round(float(np.percentile(v, 97.5)), 4)] if len(v) else [float("nan")] * 2


def validate_enrichment(risk, flag, outcome, clusters) -> dict:
    """risk: continuous firewall locus-risk per site; flag: 1 if the firewall intercepts the site's gene; outcome:
    1 if the site is outcome-associated (tumor); clusters: the site's gene (the resample unit). Returns OR + AUROC
    with gene-clustered bootstrap CIs and the pre-registered gate."""
    import numpy as np
    risk, flag, outcome = np.asarray(risk, float), np.asarray(flag, int), np.asarray(outcome, int)
    auroc = round(_auroc(outcome, risk), 4)
    orr = round(_odds_ratio(flag, outcome), 4)
    auroc_ci = _cluster_boot(lambda w: _auroc(outcome, risk, w), clusters)
    or_ci = _cluster_boot(lambda w: _odds_ratio(flag, outcome, w), clusters)
    gate = bool((or_ci[0] > 1.0) or (auroc_ci[0] > 0.5))
    return {"n_sites": int(len(outcome)), "n_outcome_pos": int(outcome.sum()), "n_genes": int(len(set(clusters))),
            "AUROC": auroc, "AUROC_CI": auroc_ci, "odds_ratio": orr, "odds_ratio_CI": or_ci,
            "gate_pass": gate,
            "gate": "OR CI excludes 1 OR AUROC CI excludes 0.5 (enrichment of firewall-flagged loci for the outcome)"}


# --------------------------------------------------------------------------------------------------------------
# locus risk per gene (the firewall's own assessment) + the relative-risk reframe
# --------------------------------------------------------------------------------------------------------------
def _gene_risk_cache():
    from bio_firewall.calibrate.conformal import risk_score
    from bio_firewall.eval.hazard_bench.score import intercepted
    from bio_firewall.intercept.spine import screen
    cache: dict[str, tuple[float, int]] = {}

    def risk_flag(gene: str) -> tuple[float, int]:
        g = (gene or "").upper()
        if g not in cache:
            v = screen({"intent": "insert a reporter cassette", "gene": g, "cell_type": "hspc"})
            cache[g] = (risk_score(v, g), int(intercepted(v["decision"])))
        return cache[g]
    return risk_flag


# --------------------------------------------------------------------------------------------------------------
# VISDB open-data floor run (VM only)
# --------------------------------------------------------------------------------------------------------------
def _nearest_gene(sites, genes, window_bp):
    """Map each (chrom,pos) site to its nearest gene within window_bp. Vectorized per chromosome via searchsorted."""
    import numpy as np
    out = np.array([None] * len(sites), dtype=object)
    for chrom, gi in genes.groupby("chrom"):
        gi = gi.sort_values("mid")
        mids = gi["mid"].to_numpy()
        names = gi["gene"].to_numpy()
        starts, ends = gi["start"].to_numpy(), gi["end"].to_numpy()
        mask = sites["chrom"].to_numpy() == chrom
        if not mask.any():
            continue
        pos = sites.loc[mask, "pos"].to_numpy()
        j = np.clip(np.searchsorted(mids, pos), 0, len(mids) - 1)
        for k in (-1, 0):                                     # check the two nearest gene midpoints
            jj = np.clip(j + k, 0, len(mids) - 1)
            within = (pos >= starts[jj] - window_bp) & (pos <= ends[jj] + window_bp)
            idx = np.where(mask)[0]
            cur = out[idx]
            out[idx] = np.where(within & (cur == None), names[jj], cur)   # noqa: E711
    return out


def run_visdb(out_dir: str = "bf_locus_outcome", visdb_dir: str | None = None,
              gene_coords: str | None = None, window_bp: int = WINDOW_BP, viruses=("HIV", "HTLV")) -> dict:
    import pandas as pd
    visdb_dir = Path(visdb_dir or os.environ.get("BF_VISDB_DIR", "")).expanduser()
    gc_path = Path(gene_coords or os.environ.get("BF_GENE_COORDS", "")).expanduser()
    wd = Path(out_dir)
    wd.mkdir(parents=True, exist_ok=True)

    gc = pd.read_parquet(gc_path)
    gc.columns = [c.lower() for c in gc.columns]
    gc = gc.rename(columns={"chromosome": "chrom", "seqname": "chrom", "gene_name": "gene", "symbol": "gene"})
    gc = gc[["gene", "chrom", "start", "end"]].dropna()
    gc["chrom"] = gc["chrom"].astype(str).str.replace("^chr", "chr", regex=True)
    gc["start"], gc["end"] = gc["start"].astype(int), gc["end"].astype(int)
    gc["mid"] = (gc["start"] + gc["end"]) // 2

    frames = []
    for v in viruses:
        p = visdb_dir / f"{v}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype=str)
        cols = {c.lower().strip(): c for c in df.columns}
        cc, sc, st = cols.get("human chromosome"), cols.get("hg38_start"), cols.get("sample type")
        if not (cc and sc and st):
            continue
        d = pd.DataFrame({"chrom": df[cc].astype(str), "pos": pd.to_numeric(df[sc], errors="coerce"),
                          "sample": df[st].astype(str).str.lower(), "virus": v})
        frames.append(d.dropna(subset=["pos"]))
    sites = pd.concat(frames, ignore_index=True)
    sites = sites[sites["chrom"].str.match(r"^chr([0-9]+|X|Y)$")].copy()
    sites["pos"] = sites["pos"].astype(int)
    sites["tumor"] = sites["sample"].str.contains("tumor|tumour|leukemi|lymphoma|atl", regex=True).astype(int)

    sites["gene"] = _nearest_gene(sites, gc, window_bp)
    mapped = sites[sites["gene"].notna()].copy()
    risk_flag = _gene_risk_cache()
    rf = mapped["gene"].map(lambda g: risk_flag(str(g)))
    mapped["risk"] = [x[0] for x in rf]
    mapped["flag"] = [x[1] for x in rf]

    res = validate_enrichment(mapped["risk"], mapped["flag"], mapped["tumor"], mapped["gene"])
    # per-virus split (HTLV→ATL is the most insertional-oncogenesis-relevant)
    per_virus = {}
    for v, g in mapped.groupby("virus"):
        if g["tumor"].nunique() > 1:
            per_virus[v] = validate_enrichment(g["risk"], g["flag"], g["tumor"], g["gene"])
    result = {
        "source": "VISDB (Tang et al. 2020, NAR 10.1093/nar/gkz867); local-only, never committed",
        "window_bp": window_bp, "viruses": list(viruses),
        "n_sites_total": int(len(sites)), "n_sites_mapped_to_gene": int(len(mapped)),
        "n_tumor_sites": int(mapped["tumor"].sum()),
        "overall": res, "per_virus": per_virus,
        "honest_status": ("ASSOCIATIVE retrospective enrichment on open VISDB data — 'tumor sample-source' is not a "
                          "causal insertional-oncogenesis outcome and is confounded by virus biology. The CAUSAL / "
                          "prospective clonal-outcome validation (controlled-access dbGaP/EGA) is DEFERRED -> "
                          "'outcome-validation pending'. A passing gate here is a floor, not a validated risk model."),
        "seed": SEED,
    }
    (wd / "results.json").write_text(json.dumps(result, indent=2, default=str))
    return result
