"""The NIST-compatible export validates against its declared schema and is deterministic;
the committed export (if present) matches; the living-KB documents its IBBIS-DSSC alignment + hooks; the OSTP note
is framed as a complementary design-stage layer."""
from __future__ import annotations

import json
from pathlib import Path

from bio_firewall.standards import OSTP_NOTE, export_benchmark, kb_standards_alignment, validate_export

_COMMITTED = Path(__file__).resolve().parents[1] / "standards" / "nist_benchmark_export.json"


def test_export_validates_against_schema():
    pkg = export_benchmark()
    rep = validate_export(pkg)
    assert rep["valid"], rep["violations"]
    assert pkg["schema"] == "nist-screening-compatible/design-stage@1"
    assert pkg["n_records"] == len(pkg["records"]) == len(pkg["answer_key"])
    assert pkg["label_vocabulary"] == ["hazard", "benign"]


def test_export_carries_no_sequences():
    pkg = export_benchmark()
    blob = json.dumps(pkg)
    import re
    assert not re.search(r"\b[ACGTUacgtu]{12,}\b", blob)            # symbols/labels only, never sequences


def test_export_is_deterministic():
    assert export_benchmark()["content_sha256"] == export_benchmark()["content_sha256"]


def test_validate_catches_tampering():
    pkg = export_benchmark()
    pkg["answer_key"][pkg["records"][0]["record_id"]]["independent_label"] = "totally-benign"
    assert not validate_export(pkg)["valid"]


def test_committed_export_matches_if_present():
    if not _COMMITTED.exists():
        return                                                     # generated on the validation host, then committed
    committed = json.loads(_COMMITTED.read_text(encoding="utf-8"))
    assert validate_export(committed)["valid"]
    assert committed["content_sha256"] == export_benchmark()["content_sha256"]


def test_kb_ibbis_alignment_documented_with_hooks_and_no_conformance_claim():
    a = kb_standards_alignment()
    assert a["conformance_claim"] is False                          # alignment intent + hooks, not certification
    assert a["hooks_pending"] and a["aligned"]
    assert all(a["fields_present"].values())                        # the aligned KB fields actually exist
    assert "DSSC" in a["standard"]


def test_ostp_note_is_complementary_design_stage():
    assert OSTP_NOTE["deadline"] == "2026-10-13"
    assert "complementary" in OSTP_NOTE["position"].lower()
    assert "not a replacement" in OSTP_NOTE["position"].lower()
