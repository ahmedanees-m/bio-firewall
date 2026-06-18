"""WS-EDIT-MECH (v0.6.0) — de-novo oncogenic-fusion detection by mechanism generalizes beyond the curated
gene-pair list, while leaving the curated hard_reject and the benign-fusion floor unchanged."""
from __future__ import annotations

from bio_firewall import screen
from bio_firewall.hazard.edit_mech import oncogenic_fusion_mechanism


def test_kinase_fusion_flagged_by_mechanism_off_list():
    # ETV6::NTRK3 is a real oncogenic fusion NOT in the curated yaml -> caught by the kinase mechanism.
    is_mech, why = oncogenic_fusion_mechanism("ETV6", "NTRK3")
    assert is_mech and "kinase" in why.lower()


def test_benign_nonkinase_pair_not_flagged_by_mechanism():
    assert oncogenic_fusion_mechanism("ZZZ1", "ZZZ2") == (False, None)   # neither kinase nor a known cancer gene


def test_edit_axis_denovo_flag_for_off_list_kinase_fusion():
    v = screen({"intent": "engineer a fusion", "edit": {"fusion_genes": ["ETV6", "NTRK3"]}})
    assert v["decision"] == "flag_for_review"
    assert v["axes"]["edit_type"]["rule_id"] == "edit.denovo_oncogenic_fusion"
    assert v["axes"]["edit_type"]["extrapolating"] is True


def test_curated_fusion_still_hard_reject():
    v = screen({"intent": "engineer a fusion", "edit": {"fusion_genes": ["BCR", "ABL1"]}})
    assert v["decision"] == "refuse"
    assert v["axes"]["edit_type"]["rule_id"] == "edit.oncogenic_fusion_by_design"


def test_benign_unknown_fusion_still_generic_floor():
    # AAVS1::CLYBL — safe-harbour pair, no kinase, no cancer role -> the generic 'unknown oncogenicity' floor, not denovo.
    v = screen({"intent": "engineer a fusion", "edit": {"fusion_genes": ["AAVS1", "CLYBL"]}})
    assert v["decision"] == "flag_for_review"
    assert v["axes"]["edit_type"]["rule_id"] == "edit.fusion_unknown_oncogenicity"
