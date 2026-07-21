"""De-novo oncogenic-fusion detection by MECHANISM, generalizing beyond the curated
gene-PAIR lookup (bio_firewall/vendored_data/oncogenic_fusions.yaml). 'AI can design what isn't catalogued', so the edit axis
must flag a rearrangement whose MECHANISM is oncogenic even when the exact pair is on no list.

Three mechanism signals (function-family level - no hazard sequences; public cancer-fusion biology):
  1. CONSTITUTIVE KINASE ACTIVATION - a recurrent fusion-kinase partner (ABL1/ALK/ROS1/RET/NTRK/FGFR/JAK2/...) is
     fused, so its kinase domain dimerizes/activates ligand-independently (BCR-ABL1, EML4-ALK, ...). Catches an
     off-list kinase fusion (e.g. a novel NTRK3 partner) the gene-pair lookup misses.
  2. ONCOGENE JUXTAPOSITION/DYSREGULATION - an oncogene/driver (CancerMine, CC0) placed under a partner's
     promoter/enhancer by the rearrangement (TMPRSS2-ERG, MYC-IGH style).
  3. IG/TCR ENHANCER JUXTAPOSITION - an immunoglobulin or T-cell-receptor locus fused to an oncogene (the classic
     lymphoma super-enhancer mechanism).

This is a NEW discriminating signal LAYERED ON the existing safety floor (every designed fusion still flags for
review); it does not relax the screen - it adds the specific mechanism + lets the benchmark measure generalization
to off-list fusions vs controlled false-positive on benign constructs."""
from __future__ import annotations

from bio_firewall.data import gene_roles

# recurrent fusion KINASES (public, textbook cancer-fusion biology) - function-family membership, not sequences.
KINASE_FUSION_GENES = frozenset({
    "ABL1", "ABL2", "ALK", "ROS1", "RET", "NTRK1", "NTRK2", "NTRK3", "FGFR1", "FGFR2", "FGFR3", "FGFR4",
    "JAK1", "JAK2", "JAK3", "PDGFRA", "PDGFRB", "PDGFB", "BRAF", "RAF1", "MET", "KIT", "FLT3", "SYK", "LTK",
    "CSF1R", "MERTK", "EGFR", "ERBB2", "FGR", "FES", "NTRK", "TYK2", "MAP3K8", "PRKCA", "PRKACA", "AKT3",
})
# immunoglobulin / T-cell-receptor loci (super-enhancer juxtaposition partners).
IG_TCR_LOCI = frozenset({"IGH", "IGH@", "IGK", "IGL", "IGK@", "IGL@", "TRA", "TRB", "TRD", "TRG",
                         "TRA@", "TRB@", "TRD@", "TRG@", "IGHV", "IGKV", "IGLV"})


def _onc(gene: str) -> bool:
    return bool(gene_roles(gene) & {"oncogene", "driver"})


def oncogenic_fusion_mechanism(gene_a: str, gene_b: str) -> tuple[bool, str | None]:
    """Is a fusion of (gene_a, gene_b) oncogenic by MECHANISM (not by curated-pair membership)? Returns
    (is_oncogenic, mechanism_text). Order-independent."""
    a, b = (gene_a or "").upper(), (gene_b or "").upper()
    ka, kb = a in KINASE_FUSION_GENES, b in KINASE_FUSION_GENES
    if ka or kb:
        kin = a if ka else b
        return True, (f"constitutive kinase activation - fusing the recurrent fusion-kinase {kin} dimerizes/activates "
                      "its kinase domain ligand-independently (BCR-ABL1 / EML4-ALK mechanism)")
    iga, igb = a in IG_TCR_LOCI, b in IG_TCR_LOCI
    if (iga and _onc(b)) or (igb and _onc(a)):
        onc = b if iga else a
        return True, f"IG/TCR super-enhancer juxtaposition driving the oncogene {onc} (MYC-IGH lymphoma mechanism)"
    if _onc(a) or _onc(b):
        onc = a if _onc(a) else b
        return True, (f"oncogene/driver {onc} placed under the fusion partner's promoter - dysregulated expression "
                      "(TMPRSS2-ERG mechanism)")
    return False, None
