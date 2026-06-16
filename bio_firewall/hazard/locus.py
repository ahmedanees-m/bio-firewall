"""Axis 2 — LOCUS (where you write) — THE EDGE. Now data-grounded on the VENDORED CC0 data (CancerMine
oncogene/TSG/driver + DepMap essential, derived from PEN-STACK v6.6.0). Flags: oncogene-activation-by-design
(hard_reject), genotoxic-CIS proximity, tumor-suppressor disruption, essential-gene disruption, oncogene proximity.

HONESTY: this axis FLAGS on mechanism; the genotoxicity proxy is NOT outcome-validated (PEN-STACK v6.5/v6.6). It
does not certify safety or output a validated cancer rate — it routes elevated risk to human review. Almost every
hazardous genome-write is also legitimate research (disrupting a TSG is standard cancer modeling) -> flag, not block."""
from __future__ import annotations

from bio_firewall.data import dosage, gene_roles
from bio_firewall.hazard.finding import Finding, finding

# well-known insertional-oncogenesis CIS genes (literature facts, not source-specific)
_GENOTOXIC_CIS = {"LMO2", "MECOM", "EVI1", "CCND2", "PRDM16", "HMGA2"}


def screen_locus(plan: dict) -> Finding:
    locus = plan.get("locus") or {}
    gene = str(locus.get("gene") or "").upper()
    intent = str(plan.get("intent") or "").lower()
    roles = gene_roles(gene)
    src = {"source": "CancerMine (CC0) + DepMap (CC BY); genotoxic-CIS literature list"}

    # hard_reject — designed oncogene activation (the SCID-X1/LMO2 mechanism)
    if "oncogene" in roles and any(w in intent for w in ("activate", "enhancer", "promoter")) and "oncogene" in intent:
        return finding("hard_reject", "locus.oncogene_activation_by_design", "locus",
                       f"insertion designed to activate the proto-oncogene {gene} via enhancer/promoter placement",
                       provenance={**src, "doi": ["10.1126/science.1088547"], "note": "SCID-X1/LMO2"})
    # genotoxic-CIS proximity — the strongest insertional-oncogenesis flag
    if gene in _GENOTOXIC_CIS:
        return finding("soft_penalty", "locus.genotoxic_proximity", "locus",
                       f"insertion at/near a genotoxic-CIS locus ({gene}) — insertional-oncogenesis risk "
                       "(SCID-X1/LMO2 precedent); mechanism-grounded flag, not a calibrated cancer rate",
                       provenance={**src, "doi": ["10.1126/science.1088547"]}, extrapolating=True)
    # tumor-suppressor disruption (misuse vector AND legitimate cancer modeling -> flag, not block)
    if "TSG" in roles:
        return finding("soft_penalty", "locus.tumor_suppressor_disruption", "locus",
                       f"disruption of a tumor suppressor ({gene}) — flag (legitimate in cancer modeling)",
                       provenance=src, extrapolating=True)
    # essential gene disruption (DepMap)
    if "essential" in roles:
        return finding("soft_penalty", "locus.essential_disruption", "locus",
                       f"disruption of a common-essential gene ({gene}) — viability risk",
                       provenance=src, extrapolating=True)
    # generic oncogene/driver proximity (CancerMine)
    if "oncogene" in roles or "driver" in roles:
        return finding("soft_penalty", "locus.oncogene_proximity", "locus",
                       f"insertion at/near an oncogene/driver ({gene}) — insertional-oncogenesis risk",
                       provenance=src, extrapolating=True)
    # dosage sensitivity / haploinsufficiency (gnomAD pLI/LOEUF) — disrupting a high-pLI gene risks LOF phenotype
    dz = dosage(gene)
    if dz and dz[0] >= 0.9:
        return finding("soft_penalty", "locus.dosage_sensitive", "locus",
                       f"disruption of a dosage-sensitive / haploinsufficient gene ({gene}; gnomAD pLI={dz[0]:.2f}"
                       + (f", LOEUF={dz[1]:.2f}" if dz[1] is not None else "") + ")",
                       provenance={"source": "gnomAD constraint (pLI/LOEUF), open aggregate data"}, extrapolating=True)
    return finding("clear", None, "locus", "no locus hazard signal (CancerMine/DepMap/gnomAD CC0/open)")
