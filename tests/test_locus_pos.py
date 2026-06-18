"""WS-LOCUS-POS (v0.6.0) - the positional screen flags an insertion in an oncogene's promoter/enhancer window
even when it lands in NO oncogene gene body (the SCID-X1/LMO2 mechanism a membership lookup misses)."""
from __future__ import annotations

from pathlib import Path

from bio_firewall import screen
from bio_firewall.hazard.locus_pos import positional_finding

_VD = Path(__file__).resolve().parents[1] / "vendored_data"
_HAS = (_VD / "oncogene_tss.parquet").exists()

# LMO2 TSS (vendored, GENCODE hg38): chr11:33,892,076 (- strand, genotoxic-CIS).
_LMO2_TSS = 33_892_076


def test_promoter_proximal_insertion_near_lmo2_is_flagged():
    if not _HAS:
        return                                            # positional reference vendored on a data build; skip
    f = positional_finding("chr11", _LMO2_TSS + 3_000)    # ~3 kb from the LMO2 TSS, no gene body
    assert f is not None and f.rule_id == "locus.promoter_proximal_oncogene"
    assert "LMO2" in f.mechanism


def test_screen_flags_coordinate_only_insertion_genebody_lookup_misses():
    if not _HAS:
        return
    # a plan with ONLY a coordinate (no gene symbol) -> the gene-membership lookup is blind; positional catches it.
    v = screen({"intent": "insert a reporter cassette", "chrom": "chr11", "pos": _LMO2_TSS + 4_000})
    assert v["decision"] == "flag_for_review"
    assert v["axes"]["locus"]["rule_id"] in ("locus.promoter_proximal_oncogene", "locus.enhancer_proximal_oncogene")


def test_insertion_far_from_any_oncogene_is_clear():
    if not _HAS:
        return
    assert positional_finding("chr11", 1_000_000) is None        # far from any oncogene TSS
    v = screen({"intent": "insert reporter", "chrom": "chr11", "pos": 1_000_000})
    assert v["decision"] == "allow"
