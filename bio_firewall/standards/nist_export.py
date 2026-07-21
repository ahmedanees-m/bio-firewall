"""NIST-compatible benchmark export. Emit BioFirewall's safe-proxy LOCUS benchmark in a shape that
mirrors the NIST baseline-screening test set's conventions: blinded record ids + a SEPARATE answer key (the NIST set
blinds FASTA headers and supplies labels separately), a declared field schema, and a content checksum - so an
external tool can run the benchmark in a recognized shape and score against the key.

Based on: NIST "test dataset for assessing baseline nucleic acid sequence screening" (ark:/88434/mds2-3787,
2025-05-21) + Laird et al. inter-tool analysis (bioRxiv 10.1101/2025.05.30.655379).

This is a DESIGN-STAGE analog, stated plainly: the records are PUBLIC gene-symbol proxies (Tier-1 clinical-CIS
loci vs benign therapeutic/safe-harbour loci), NOT sequences and NOT hazards. BioFirewall is a design-stage screen,
complementary to the synthesis-stage sequence screening the NIST set targets; the alignment is to the dataset
CONVENTIONS, not a claim to be a synthesis screener."""
from __future__ import annotations

import hashlib
import json
import re

from bio_firewall.eval.hazard_bench.oracles import TIER1_CLINICAL_CIS

_SCHEMA = "nist-screening-compatible/design-stage@1"

# Benign LOCUS proxies: standard gene-therapy targets / safe-harbour loci that are NOT insertional-oncogenesis loci
# by the independent clinical-CIS criterion. Public gene symbols, no sequences.
_BENIGN_LOCI = ("AAVS1", "CCR5", "HBB", "F9", "CFTR", "DMD", "HEXA", "PAH", "G6PC", "SERPINA1")

_NT_RUN = re.compile(r"\b[ACGTUacgtu]{12,}\b")           # a leaked nucleotide sequence (must NOT appear)
_REC_ID = re.compile(r"^BF-\d{5}$")


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()


def export_benchmark() -> dict:
    """Build the NIST-compatible export package (records + answer key + schema + checksum)."""
    records: list[dict] = []
    answer_key: dict[str, dict] = {}
    i = 0
    for g in sorted(TIER1_CLINICAL_CIS):
        rid = f"BF-{i:05d}"
        records.append({"record_id": rid, "axis": "locus",
                        "plan": {"intent": "locus screening proxy", "gene": g, "cell_type": "hspc"}})
        ctx, doi = TIER1_CLINICAL_CIS[g]
        answer_key[rid] = {"independent_label": "hazard", "stratum": "tier1_clinical_cis",
                           "provenance": {"context": ctx, "doi": doi}}
        i += 1
    for g in _BENIGN_LOCI:
        rid = f"BF-{i:05d}"
        records.append({"record_id": rid, "axis": "locus",
                        "plan": {"intent": "locus screening proxy", "gene": g, "cell_type": "hspc"}})
        answer_key[rid] = {"independent_label": "benign", "stratum": "benign_therapeutic_or_safe_harbour",
                           "provenance": {"context": "non-insertional-oncogenesis therapeutic/safe-harbour locus"}}
        i += 1

    pkg = {
        "schema": _SCHEMA,
        "title": "BioFirewall safe-proxy locus benchmark (NIST-baseline-screening-compatible shape)",
        "based_on": ["NIST test dataset for assessing baseline nucleic acid sequence screening "
                     "(ark:/88434/mds2-3787, 2025-05-21)",
                     "Laird et al., inter-tool analysis (bioRxiv 10.1101/2025.05.30.655379, 2025)"],
        "design_stage_note": ("design-stage analog: blinded record ids + a SEPARATE answer key (mirrors the NIST "
                              "blinded-header convention). Records are PUBLIC gene-symbol proxies, NO sequences and "
                              "NO hazards. BioFirewall screens design-stage plans; it is complementary to, not a "
                              "replacement for, synthesis-stage sequence screening."),
        "fields": {
            "record_id": "opaque blinded id, ^BF-\\d{5}$",
            "axis": "the screening axis (locus)",
            "plan": "a design-stage plan {intent, gene, cell_type} - a public proxy, never a sequence",
            "answer_key[record_id]": "{independent_label in {hazard,benign}, stratum, provenance}",
        },
        "label_vocabulary": ["hazard", "benign"],
        "n_records": len(records),
        "records": records,
        "answer_key": answer_key,
    }
    pkg["content_sha256"] = hashlib.sha256(_canonical({k: v for k, v in pkg.items()})).hexdigest()
    return pkg


def validate_export(pkg: dict) -> dict:
    """Validate a package against the declared schema. Returns {valid, violations}. Checks: schema id, blinded id
    format, record<->answer-key bijection, label vocabulary, NO sequences leaked, and checksum integrity."""
    v: list[str] = []
    if pkg.get("schema") != _SCHEMA:
        v.append(f"schema != {_SCHEMA}")
    records = pkg.get("records", [])
    key = pkg.get("answer_key", {})
    rec_ids = {r.get("record_id") for r in records}
    for r in records:
        if not _REC_ID.match(str(r.get("record_id", ""))):
            v.append(f"bad record_id {r.get('record_id')!r}")
        if "plan" not in r or "axis" not in r:
            v.append(f"record {r.get('record_id')} missing axis/plan")
    if rec_ids != set(key):
        v.append("records and answer_key are not a bijection")
    if any(key[k].get("independent_label") not in ("hazard", "benign") for k in key):
        v.append("answer_key carries a label outside {hazard,benign}")
    # no sequences may leak anywhere in the package (design-stage; signatures/symbols only)
    if _NT_RUN.search(json.dumps({"records": records, "answer_key": key}, default=str)):
        v.append("a nucleotide sequence leaked into the export (must be symbols/labels only)")
    expect = hashlib.sha256(_canonical({k: val for k, val in pkg.items() if k != "content_sha256"})).hexdigest()
    if pkg.get("content_sha256") != expect:
        v.append("content_sha256 mismatch")
    return {"valid": not v, "violations": v}
