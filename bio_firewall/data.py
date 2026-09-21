"""Loads the VENDORED, license-clean (CC0) hazard data: CancerMine oncogene/TSG/driver + DepMap essential
(bio_firewall/vendored_data/locus_genes.parquet, derived from PEN-STACK) + the genotoxicity oracle. NO restricted
source is vendored (a CI test enforces this). The legal crux: the gene *list* is from a CC0 compilation."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_VD = Path(__file__).resolve().parent / "vendored_data"


@lru_cache(maxsize=1)
def _gene_roles() -> dict[str, set[str]]:
    """gene (UPPER) -> set of roles {oncogene, TSG, driver, essential}. Empty if the vendored file is absent."""
    p = _VD / "locus_genes.parquet"
    if not p.exists():
        return {}
    import pandas as pd
    df = pd.read_parquet(p)
    out: dict[str, set[str]] = {}
    for gene, role in zip(df["gene"].astype(str), df["role"].astype(str)):
        out.setdefault(gene.upper(), set()).update(role.split(","))
    return out


def gene_roles(gene: str) -> set[str]:
    """The CancerMine/DepMap roles of a gene (oncogene / TSG / driver / essential), CC0."""
    return _gene_roles().get(str(gene or "").upper(), set())


@lru_cache(maxsize=1)
def _dosage() -> dict[str, tuple[float, float | None]]:
    """gene (UPPER) -> (pLI, LOEUF) from gnomAD constraint (open aggregate data). pLI>=0.9 = haploinsufficient."""
    p = _VD / "gnomad_constraint.parquet"
    if not p.exists():
        return {}
    import pandas as pd
    df = pd.read_parquet(p)
    return {str(g).upper(): (float(pli), (float(lo) if lo == lo else None))
            for g, pli, lo in zip(df["gene"], df["pLI"], df["LOEUF"])}


def dosage(gene: str) -> tuple[float, float | None] | None:
    """gnomAD (pLI, LOEUF) for a gene, or None. pLI>=0.9 => dosage-sensitive / haploinsufficient."""
    return _dosage().get(str(gene or "").upper())


@lru_cache(maxsize=1)
def _oncogene_tss() -> dict:
    """chrom -> (sorted TSS array, gene array, role array) for the oncogene/driver/genotoxic-CIS TSS reference
    (GENCODE coords x CancerMine CC0 roles). Powers the positional locus screen. Empty if not vendored."""
    p = _VD / "oncogene_tss.parquet"
    if not p.exists():
        return {}
    import pandas as pd
    df = pd.read_parquet(p)
    out: dict = {}
    for chrom, g in df.groupby("chrom"):
        g = g.sort_values("tss")
        out[str(chrom)] = (g["tss"].to_numpy(), g["gene"].astype(str).to_numpy(), g["role"].astype(str).to_numpy())
    return out


def nearest_oncogene_tss(chrom: str, pos: int) -> tuple[str, int, str, int] | None:
    """Nearest oncogene TSS to (chrom, pos): (gene, tss, role, distance_bp), or None. For positional locus risk."""
    import numpy as np
    d = _oncogene_tss().get(str(chrom))
    if d is None:
        return None
    tss, genes, roles = d
    j = int(np.clip(np.searchsorted(tss, pos), 0, len(tss) - 1))
    best = None
    for k in (j - 1, j):
        if 0 <= k < len(tss):
            dist = abs(int(tss[k]) - int(pos))
            if best is None or dist < best[3]:
                best = (str(genes[k]), int(tss[k]), str(roles[k]), dist)
    return best


@lru_cache(maxsize=1)
def oncogenic_fusions() -> dict[str, dict]:
    """Curated open set of canonical oncogenic gene fusions. Key = sorted gene pair 'A::B'."""
    p = _VD / "oncogenic_fusions.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")).get("fusions", {})) if p.exists() else {}


def is_oncogenic_fusion(gene_a: str, gene_b: str) -> dict | None:
    """The fusion record if {gene_a, gene_b} is a known oncogenic fusion, else None (order-independent)."""
    key = "::".join(sorted([str(gene_a or "").upper(), str(gene_b or "").upper()]))
    return oncogenic_fusions().get(key)


@lru_cache(maxsize=1)
def genotox_oracle() -> dict:
    p = _VD / "genotoxicity_oracle.yaml"
    return yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}


# ---------------------------------------------------------------------------------------------
# Vendored-resource status
# ---------------------------------------------------------------------------------------------
# Each loader above returns an empty mapping when its file is absent, so a rule that depends on it
# stops matching rather than failing. That keeps the package importable in a partial install, but
# on its own it disables a hazard rule without saying so. These helpers make the absence visible,
# and BIOFW_REQUIRE_VENDORED_DATA makes it fatal for deployments that want to fail closed.
_REQUIRED = {
    "locus_genes.parquet": "gene roles (oncogene / TSG / driver / essential)",
    "gnomad_constraint.parquet": "dosage sensitivity",
    "oncogene_tss.parquet": "positional locus screen",
    "oncogenic_fusions.yaml": "oncogenic fusion rule",
    "genotoxicity_oracle.yaml": "genotoxicity rule",
}


def vendored_status() -> dict[str, bool]:
    """Which vendored hazard resources are present. False means the rule it powers is inactive."""
    return {name: (_VD / name).exists() for name in _REQUIRED}


def missing_vendored() -> list[str]:
    """Vendored hazard resources that are absent, and so silently disable a rule."""
    return sorted(n for n, ok in vendored_status().items() if not ok)


def require_vendored_data() -> None:
    """Raise when a hazard resource is missing and the deployment asked to fail closed."""
    import os
    if not os.getenv("BIOFW_REQUIRE_VENDORED_DATA"):
        return
    missing = missing_vendored()
    if missing:
        detail = ", ".join(f"{m} ({_REQUIRED[m]})" for m in missing)
        raise RuntimeError(
            f"vendored hazard data missing, so the corresponding rules are inactive: {detail}. "
            "Unset BIOFW_REQUIRE_VENDORED_DATA to run in a degraded configuration.")
