"""WS-LIVING-KB (v0.7.0) — the versioned, signed hazard knowledge base. The hazard signatures (genotoxic-CIS loci,
oncogenic fusion pairs, recurrent fusion-kinases, IG/TCR loci) are consolidated into ONE versioned resource with
per-signature provenance, an integrity digest, and an HMAC signature — the antivirus-signatures-update model, so the
KB can be maintained and contributed to as new threats are characterized (see docs/HAZARD_KB.md)."""
from bio_firewall.kb.registry import (  # noqa: F401
    content_digest, entries, latest_version, load_kb, sign_kb, verify_kb,
)

__all__ = ["load_kb", "verify_kb", "sign_kb", "content_digest", "entries", "latest_version"]
