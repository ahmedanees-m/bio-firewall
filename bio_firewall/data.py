"""Loads the VENDORED, license-clean (CC0) hazard data: CancerMine oncogene/TSG/driver + DepMap essential
(vendored_data/locus_genes.parquet, derived from PEN-STACK v6.6.0) + the genotoxicity oracle. NO restricted
source is vendored (a CI test enforces this). The legal crux: the gene *list* is from a CC0 compilation."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

_VD = Path(__file__).resolve().parent.parent / "vendored_data"


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
