"""WS-LIVING-KB (v0.7.0) — the signed hazard KB verifies, every entry carries provenance, and the KB is a SUPERSET
of the in-code signatures (it cannot silently drift from what the screen actually uses)."""
from __future__ import annotations

from bio_firewall.hazard.edit_mech import IG_TCR_LOCI, KINASE_FUSION_GENES
from bio_firewall.hazard.locus import _GENOTOXIC_CIS
from bio_firewall.kb import content_digest, entries, load_kb, verify_kb

_KB = load_kb()
_HAS = bool(_KB)


def test_kb_signature_and_digest_verify():
    if not _HAS:
        return                                            # KB vendored on a data build; skip on a bare checkout
    assert verify_kb(_KB) is True
    assert _KB["content_sha256"] == content_digest(_KB)


def test_kb_tamper_breaks_signature():
    if not _HAS:
        return
    bad = dict(_KB)
    bad["entries"] = _KB["entries"][:-1]                  # drop one signature -> integrity + HMAC must fail
    assert content_digest(bad) != _KB["content_sha256"]
    assert verify_kb(bad) is False


def test_every_entry_has_provenance():
    if not _HAS:
        return
    for e in _KB["entries"]:
        assert e.get("id") and e.get("type") and e.get("value")
        assert e.get("provenance") and any(e["provenance"].get(k) for k in ("source", "doi", "citation"))


def test_kb_is_superset_of_in_code_signatures():
    """The KB must contain every signature the code screens on (no silent drift)."""
    if not _HAS:
        return
    cis = {e["value"] for e in entries(_KB, "genotoxic_cis_locus")}
    kin = {e["value"] for e in entries(_KB, "fusion_kinase")}
    ig = {e["value"] for e in entries(_KB, "ig_tcr_locus")}
    assert _GENOTOXIC_CIS <= cis
    assert KINASE_FUSION_GENES <= kin
    assert IG_TCR_LOCI <= ig
