"""Independent hazard-labeling oracles — the DE-CIRCULARIZATION core of Benchmark 1.

The firewall flags loci via CancerMine + DepMap + gnomAD (its vendored data). The benchmark must therefore LABEL
hazard from sources the firewall DOES NOT use, so a high score means the firewall *generalized* to an independent
definition of hazard — not that it recognized its own gene list (the v0.3 demo's tautology).

Two tiers:
  - TIER-1 (GOLD): genes implicated in ACTUAL insertional-oncogenesis ADVERSE EVENTS in human gene-therapy trials.
    Hand-curated literature facts (gene symbol + primary DOI) — public knowledge, safe to commit. This is *measured
    harm*; the firewall MUST catch 100% of these (the named, mandatory gate).
  - TIER-2 (BROAD): independent expert annotations — COSMIC Cancer Gene Census (v104) + NCG. These are LICENSE-
    RESTRICTED data: loaded from a LOCAL path (`BF_BENCH_ORACLES`, default ../../bench_oracles), gitignored, NEVER
    committed. If absent, the loaders return empty and the broad benchmark is skipped with a clear message.

Nothing here is shipped as data except the Tier-1 literature list (gene symbols + DOIs)."""
from __future__ import annotations

import csv
import os
from functools import lru_cache
from pathlib import Path

# --- TIER-1: clinical insertional-oncogenesis genes (real adverse events). gene -> (trial context, primary DOI). ---
# These are the loci near which retroviral/lentiviral vector integration drove clonal expansion / leukemia / MDS in
# actual patients. Curated from the gene-therapy safety literature (public facts).
TIER1_CLINICAL_CIS: dict[str, tuple[str, str]] = {
    "LMO2":   ("SCID-X1 gammaretroviral trials — T-ALL in 5 children", "10.1126/science.1088547"),
    "CCND2":  ("SCID-X1 / WAS — clonal expansion", "10.1172/JCI35798"),
    "MECOM":  ("CGD & WAS — MDS1-EVI1 activation, clonal dominance/MDS", "10.1038/nm.2088"),
    "EVI1":   ("CGD — EVI1 activation, clonal dominance", "10.1038/nm.2088"),
    "MDS1":   ("CGD — MDS1-EVI1 locus activation", "10.1038/nm.2088"),
    "PRDM16": ("CGD — clonal dominance", "10.1038/nm.2088"),
    "SETBP1": ("CGD — clonal expansion", "10.1038/nm.2088"),
    "HMGA2":  ("beta-thalassemia lentiviral trial — clonal dominance", "10.1038/nature09328"),
    "BMI1":   ("integration-site clonal expansion (CGD/WAS analyses)", "10.1126/scitranslmed.3007280"),
    "MN1":    ("WAS gammaretroviral trial — clonal expansion", "10.1126/scitranslmed.3007280"),
    "CCND1":  ("WAS / SCID — proto-oncogene activation precedent", "10.1126/scitranslmed.3007280"),
    "LMO1":   ("LMO-family activation precedent (paralog of LMO2)", "10.1126/science.1088547"),
}


def _oracle_dir() -> Path:
    env = os.environ.get("BF_BENCH_ORACLES")
    if env:
        return Path(env)
    # default: ../../bench_oracles relative to the repo root (OUTSIDE the repo tree)
    return Path(__file__).resolve().parents[3].parent / "bench_oracles"


@lru_cache(maxsize=1)
def tier1_genes() -> frozenset[str]:
    return frozenset(TIER1_CLINICAL_CIS)


@lru_cache(maxsize=1)
def cosmic_cgc() -> dict[str, str]:
    """COSMIC Cancer Gene Census v104: gene (UPPER) -> ROLE_IN_CANCER. Local-only; {} if absent. NEVER committed."""
    p = _oracle_dir() / "cosmic_cgc_v104.tsv"
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    with p.open(encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            g = (r.get("GENE_SYMBOL") or "").strip().upper()
            if g:
                out[g] = (r.get("ROLE_IN_CANCER") or "").strip()
    return out


@lru_cache(maxsize=1)
def cosmic_genes() -> frozenset[str]:
    return frozenset(cosmic_cgc())


@lru_cache(maxsize=1)
def cosmic_oncogenes() -> frozenset[str]:
    return frozenset(g for g, role in cosmic_cgc().items() if "oncogene" in role.lower())


@lru_cache(maxsize=1)
def cosmic_fusion_genes() -> frozenset[str]:
    """Genes COSMIC annotates as participating in oncogenic fusions — the independent edit-axis label."""
    return frozenset(g for g, role in cosmic_cgc().items() if "fusion" in role.lower())


def independent_hazard_genes() -> frozenset[str]:
    """The union independent hazard label for the locus axis: Tier-1 clinical CIS + COSMIC CGC."""
    return frozenset(tier1_genes() | cosmic_genes())


def oracle_status() -> dict:
    """Human-readable provenance of what loaded (printed into the report; no data leakage)."""
    return {
        "tier1_clinical_cis": len(tier1_genes()),
        "cosmic_cgc_v104": len(cosmic_genes()),
        "cosmic_oncogene_tagged": len(cosmic_oncogenes()),
        "cosmic_fusion_tagged": len(cosmic_fusion_genes()),
        "oracle_dir": str(_oracle_dir()),
        "cosmic_present": bool(cosmic_genes()),
    }
