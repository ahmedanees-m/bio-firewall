"""IBBIS-DSSC alignment + the OSTP interagency-window note (WS-STANDARDS).

The living hazard-KB (vendored_data/hazard_kb/<v>.yaml) is described against the IBBIS DNA Screening Standards
Consortium (DSSC, launched 2025-11-06) and its Common Mechanism lineage: where the standard is published we map the
KB fields to it; where it is still forming we declare an explicit HOOK and make NO conformance claim (the standard is
a moving target). This is alignment INTENT + hooks, not certification."""
from __future__ import annotations

from bio_firewall.kb.registry import load_kb

# The OSTP interagency-window note: design-stage governance as a layer COMPLEMENTARY to synthesis-stage screening.
# Framed precisely - not a replacement for, nor an implementation of, the synthesis framework. Deadline is the
# framework's own state-of-the-art assessment milestone.
OSTP_NOTE = {
    "window": "US interagency state-of-the-art assessment of nucleic-acid-synthesis screening",
    "authority": "Framework for Nucleic Acid Synthesis Screening (OSTP, 2024-04-29, Section 4.4(b)(i))",
    "deadline": "2026-10-13",
    "caveat": ("the 2024 Framework may be revised or replaced per the 2025-05-05 Executive Order 'Improving the "
               "Safety and Security of Biological Research'; this note aligns with a moving target."),
    "position": ("BioFirewall is a DESIGN-STAGE governance layer (it screens genome-writing plans before synthesis "
                 "and signs a passport) that is COMPLEMENTARY to synthesis-stage sequence screening (Wittmann et al., "
                 "Science 2025, 10.1126/science.adu8578). It is not a replacement for, nor an implementation of, the "
                 "synthesis-screening framework; the two layers compose."),
}


def kb_standards_alignment(version: str | None = None) -> dict:
    """Document the living-KB's alignment to the IBBIS DSSC: which KB fields map to published standard concepts, and
    which carry an explicit hook pending the standard. Reads the committed KB to confirm the aligned fields exist."""
    kb = load_kb(version)
    present = {
        "type": bool(kb.get("entries")) and all("type" in e for e in kb["entries"]),
        "provenance": bool(kb.get("entries")) and all("provenance" in e for e in kb["entries"]),
        "versioned_release": all(k in kb for k in ("kb_version", "released", "schema_version")),
        "signed_integrity": all(k in kb for k in ("content_sha256", "hmac_sha256")),
    }
    return {
        "standard": "IBBIS DNA Screening Standards Consortium (DSSC), launched 2025-11-06",
        "related": ["IBBIS Common Mechanism for DNA Synthesis Screening",
                    "Sequence Biosecurity Risk Consortium (sequences-of-concern definition)"],
        "kb_version": kb.get("kb_version"),
        "aligned": {                                     # BF-KB field -> DSSC / Common-Mechanism concept
            "entries[].type": "sequence/function-of-concern category (Common-Mechanism style)",
            "entries[].provenance": "auditable provenance + citation basis",
            "kb_version / released / schema_version": "a versioned standard release",
            "content_sha256 + hmac_sha256": "integrity digest + signed release (tamper-evident)",
        },
        "fields_present": present,
        "hooks_pending": {                               # explicit hooks where the DSSC standard is still forthcoming
            "dssc_validated_test_set_id": "map the BF safe-proxy benchmark ids to a DSSC validated-test-set id when "
                                          "the consortium publishes one",
            "soc_taxonomy_crosswalk": "crosswalk BF hazard `type` values to the DSSC sequence-of-concern taxonomy "
                                      "once finalized",
        },
        "conformance_claim": False,                      # alignment intent + hooks; NOT a conformance claim
    }
