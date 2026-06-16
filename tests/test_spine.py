"""Phase-0 acceptance: the governance spine screens artifacts across the five axes and stratifies honestly.
CI-safe: the cargo axis falls back gracefully if the PEN-STACK Guardian isn't importable."""
from __future__ import annotations

from bio_firewall import screen


def test_benign_somatic_plan_is_allowed():
    v = screen({"intent": "insert a therapeutic FIX cassette", "gene": "AAVS1",
                "cell_type": "hepatocyte", "delivery_vehicle": "AAV_single"})
    assert v["decision"] == "allow"
    assert v["axes"]["germline"]["decision"] == "clear"
    assert v["passport"]["decision"] == "allow" and v["passport"]["signature"]


def test_human_heritable_clinical_is_refused():
    # Axis 4 (germline, the new axis): human heritable clinical edit -> hard_reject -> refuse.
    v = screen({"intent": "clinical embryo edit", "gene": "CCR5",
                "germline": {"cell_type": "zygote", "organism": "human", "clinical": True}})
    assert v["decision"] == "refuse"
    assert v["axes"]["germline"]["rule_id"] == "germline.human_heritable_clinical"


def test_embryo_research_is_flagged_for_oversight_not_blocked():
    v = screen({"intent": "research", "germline": {"cell_type": "embryo", "organism": "human"}})
    assert v["decision"] == "flag_for_review"            # scope_flag -> review, NOT a hard block (usability gate)
    assert v["axes"]["germline"]["decision"] == "scope_flag"


def test_genotoxic_locus_is_flagged_with_mechanism_not_predicted():
    v = screen({"intent": "knock-in study", "gene": "LMO2", "cell_type": "hspc"})
    assert v["decision"] == "flag_for_review"            # legitimate research -> flagged, not blocked
    f = v["axes"]["locus"]
    assert f["rule_id"] == "locus.genotoxic_proximity" and f["extrapolating"] is True   # mechanism flag, not prediction


def test_megabase_scale_amplifies_to_review():
    v = screen({"intent": "large rearrangement", "scale": {"total_bp": 2_000_000}})
    assert v["decision"] == "flag_for_review"
    assert v["axes"]["scale"]["rule_id"] == "scale.megabase_restructuring"


def test_stratification_is_not_a_blocklist():
    # a declared legitimate-research proxy on a tumour-suppressor study must be FLAGGED, not blocked.
    v = screen({"intent": "cancer modeling: disrupt a tumor suppressor", "gene": "TP53", "cell_type": "k562"})
    assert v["decision"] in ("allow", "flag_for_review")   # never 'refuse' for legitimate research
