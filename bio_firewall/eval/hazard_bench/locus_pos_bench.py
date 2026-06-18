"""Benchmark 9 (v0.6.0) - WS-LOCUS-POS coverage. On real VISDB integration sites, how many does the POSITIONAL
screen flag (promoter/enhancer-proximal to an oncogene TSS) that the gene-BODY membership lookup misses (the
insertion is not inside an oncogene's coding body)? That gap is the SCID-X1/LMO2 mechanism made concrete.

The outcome-AUROC-improvement claim is DEFERRED (no validated integration-site outcome data - controlled-access,
deferred). This reports a COUNT, not a validated rate. Needs the local VISDB + gene coords + the vendored
oncogene_tss reference (VM)."""
from __future__ import annotations

import json
import os
from pathlib import Path

from bio_firewall.data import gene_roles
from bio_firewall.hazard.locus import _GENOTOXIC_CIS
from bio_firewall.hazard.locus_pos import positional_finding


def _genebody_oncogene(gene) -> bool:
    g = (str(gene) if gene is not None else "").upper()
    return bool(g) and (g in _GENOTOXIC_CIS or bool(gene_roles(g) & {"oncogene", "driver"}))


def run_visdb(out_dir: str = "bf_locus_pos", visdb_dir: str | None = None,
              gene_coords: str | None = None, viruses=("HIV", "HTLV")) -> dict:
    import pandas as pd
    from bio_firewall.eval.hazard_bench.locus_outcome import _nearest_gene
    visdb_dir = Path(visdb_dir or os.environ.get("BF_VISDB_DIR", "")).expanduser()
    gc_path = Path(gene_coords or os.environ.get("BF_GENE_COORDS", "")).expanduser()
    wd = Path(out_dir)
    wd.mkdir(parents=True, exist_ok=True)

    gc = pd.read_parquet(gc_path)
    gc.columns = [c.lower() for c in gc.columns]
    gc = gc.rename(columns={"gene_name": "gene", "symbol": "gene"})[["gene", "chrom", "start", "end"]].dropna()
    gc["chrom"] = gc["chrom"].astype(str)
    gc["start"], gc["end"] = gc["start"].astype(int), gc["end"].astype(int)
    gc["mid"] = (gc["start"] + gc["end"]) // 2

    frames = []
    for v in viruses:
        p = visdb_dir / f"{v}.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p, dtype=str)
        cols = {c.lower().strip(): c for c in df.columns}
        cc, sc = cols.get("human chromosome"), cols.get("hg38_start")
        if cc and sc:
            frames.append(pd.DataFrame({"chrom": df[cc].astype(str),
                                        "pos": pd.to_numeric(df[sc], errors="coerce")}).dropna())
    sites = pd.concat(frames, ignore_index=True)
    sites = sites[sites["chrom"].str.match(r"^chr([0-9]+|X|Y)$")].copy()
    sites["pos"] = sites["pos"].astype(int)

    sites["body_gene"] = _nearest_gene(sites, gc, window_bp=0)            # gene whose BODY contains the site (or None)
    sites["genebody_onco"] = sites["body_gene"].map(_genebody_oncogene)
    sites["pos_flag"] = [positional_finding(c, p) is not None for c, p in zip(sites["chrom"], sites["pos"])]

    n = len(sites)
    n_pos = int(sites["pos_flag"].sum())
    n_body = int(sites["genebody_onco"].sum())
    missed = sites[sites["pos_flag"] & ~sites["genebody_onco"]]          # positional catches, gene-body misses
    examples = []
    for _, r in missed.head(8).iterrows():
        nf = positional_finding(r["chrom"], int(r["pos"]))
        examples.append({"chrom": r["chrom"], "pos": int(r["pos"]), "rule": nf.rule_id, "why": nf.mechanism[:90]})

    result = {
        "n_sites": n, "n_positional_flag": n_pos, "n_genebody_oncogene": n_body,
        "n_positional_caught_genebody_missed": int(len(missed)),
        "pct_positional_adds_over_genebody": round(100 * len(missed) / max(1, n_pos), 1),
        "examples_genebody_missed": examples,
        "note": ("positional flags promoter/enhancer-proximal insertions a gene-BODY lookup misses (the LMO2 "
                 "mechanism). COUNT only - the outcome-AUROC-improvement claim is DEFERRED (controlled-access "
                 "integration-site outcome data deferred 2026-06-18; the open VISDB floor was the wrong virus biology)."),
        "source": "VISDB (10.1093/nar/gkz867) x GENCODE TSS x CancerMine roles; all local-only",
    }
    (wd / "results.json").write_text(json.dumps(result, indent=2, default=str))
    return result
