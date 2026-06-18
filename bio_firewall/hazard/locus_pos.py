"""WS-LOCUS-POS (v0.6.0) — sub-gene POSITIONAL resolution for the locus axis. A gene-membership lookup asks 'is
the target gene an oncogene?' — but the SCID-X1 LMO2 leukemias were driven by vector integration in the upstream
PROMOTER/ENHANCER region, activating LMO2 in trans; the insertion was not in an oncogene's coding body, so a
membership lookup is structurally blind to it. This screen takes the insertion COORDINATE and flags it when it
falls in the promoter / upstream-regulatory window of an oncogene TSS (GENCODE coords × CancerMine CC0 roles).

HONESTY: this adds positional FEATURES + mechanism-flagging. The outcome-AUROC-improvement claim from the v0.5
WS-LOCUS-OUTCOME plan is DEFERRED — it depends on controlled-access integration-site outcome data (deferred per the
2026-06-18 decision; the open VISDB floor was the wrong virus biology). So this flags on mechanism, not a validated
rate; the benchmark reports the COUNT of enhancer/promoter-proximal insertions a gene-body lookup misses."""
from __future__ import annotations

from bio_firewall.data import nearest_oncogene_tss
from bio_firewall.hazard.finding import Finding, finding

PROMOTER_WINDOW = 10_000        # bp from the TSS: core promoter / proximal-enhancer (insertional activation)
ENHANCER_WINDOW = 50_000        # bp: upstream regulatory / enhancer window (the LMO2 SCID-X1 distance scale)
_SRC = {"source": "GENCODE TSS × CancerMine (CC0) oncogene/driver roles; genotoxic-CIS literature list"}


def positional_finding(chrom: str, pos) -> Finding | None:
    """A locus finding from the insertion COORDINATE alone (no gene-body hit needed), or None."""
    if not chrom or pos in (None, ""):
        return None
    near = nearest_oncogene_tss(str(chrom), int(pos))
    if near is None:
        return None
    gene, _tss, role, dist = near
    if dist <= PROMOTER_WINDOW:
        dec = "scope_flag" if role == "genotoxic_cis" else "soft_penalty"
        return finding(dec, "locus.promoter_proximal_oncogene", "locus",
                       f"insertion {dist:,} bp from the {role.replace('_', '-')} {gene} TSS — promoter-proximal "
                       "oncogene-activation risk (the SCID-X1/LMO2 mechanism); a gene-body lookup misses this",
                       provenance=_SRC, extrapolating=True)
    if dist <= ENHANCER_WINDOW and role in ("genotoxic_cis", "oncogene"):
        return finding("soft_penalty", "locus.enhancer_proximal_oncogene", "locus",
                       f"insertion {dist:,} bp from the {role.replace('_', '-')} {gene} TSS — within the upstream "
                       "regulatory/enhancer window; enhancer-mediated activation risk (positional)",
                       provenance=_SRC, extrapolating=True)
    return None
