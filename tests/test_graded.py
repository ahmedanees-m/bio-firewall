"""The allow/partial/flag_for_review/refuse taxonomy maps deterministically + totally from the
per-axis verdicts, and the `partial` content gate rejects actionable/operational detail while passing general prose."""
from __future__ import annotations

from bio_firewall import screen
from bio_firewall.respond import GRADES, content_gate, grade, graded_response, partial_response

_ALLOW = {"intent": "insert a therapeutic FIX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"}
_PARTIAL = {"intent": "knock-in study", "gene": "LMO2", "cell_type": "hspc"}                  # single locus soft flag
_EMBRYO = {"intent": "research", "germline": {"cell_type": "embryo", "organism": "human"}}     # germline scope_flag
_REFUSE = {"intent": "clinical embryo edit", "gene": "CCR5",
           "germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}


def test_grade_is_total_over_decisions():
    for d in ("allow", "flag_for_review", "refuse"):
        assert grade({"decision": d, "axes": {}}) in GRADES


def test_allow_and_refuse_pass_through():
    assert grade(screen(_ALLOW)) == "allow"
    assert grade(screen(_REFUSE)) == "refuse"


def test_single_locus_mechanism_flag_is_partial():
    v = screen(_PARTIAL)
    assert v["decision"] == "flag_for_review"
    assert grade(v) == "partial" and v["grade"] == "partial"


def test_germline_scope_flag_escalates_to_full_review():
    v = screen(_EMBRYO)
    assert v["decision"] == "flag_for_review"
    assert grade(v) == "flag_for_review"                 # sensitive axis (germline) + scope_flag -> not partial


def test_cooccurring_flags_escalate_to_full_review():
    v = screen({"intent": "large knock-in", "gene": "LMO2", "cell_type": "hspc", "scale": {"total_bp": 2_000_000}})
    assert grade(v) == "flag_for_review"                 # locus + scale -> two axes -> full review


def test_grade_is_deterministic():
    v = screen(_PARTIAL)
    assert grade(v) == grade(v) == "partial"


def test_partial_response_passes_content_gate():
    v = screen(_PARTIAL)
    pr = partial_response(v)
    assert pr["actionable_detail_withheld"] is True
    assert content_gate(pr)["clean"] is True
    gr = graded_response(v)
    assert gr["grade"] == "partial" and gr["content_gate"]["clean"]


def test_content_gate_flags_actionable_detail():
    assert content_gate("insert at chr11:33892100 using the cassette")["violations"] == ["genomic_coordinate"]
    assert content_gate("the spacer is ACGTACGTACGTACGT")["clean"] is False
    assert content_gate("5'-ACGTGGATCC primer")["clean"] is False
    assert "numbered_protocol" in content_gate("Step 3: ligate the fragment")["violations"]
    assert "restriction_site" in content_gate("cut at the GAATTC site")["violations"]


def test_content_gate_passes_general_prose():
    assert content_gate("insertion at/near a genotoxic-CIS locus (LMO2) - insertional-oncogenesis risk")["clean"]
