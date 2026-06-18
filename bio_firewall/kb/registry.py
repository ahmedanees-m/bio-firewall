"""Versioned, signed hazard-KB loader + verifier. A KB release is a YAML in vendored_data/hazard_kb/<version>.yaml:

  kb_version, released, schema_version, entries:[{id, type, value, provenance, added_in}, ...],
  content_sha256  (keyless integrity digest - anyone reproduces it),
  hmac_sha256     (HMAC over the same canonical content - tamper-evident signature).

content_sha256 is the reproducible integrity check (committed + CI-verified). hmac_sha256 adds a signed release with
a key (a public default key here for integrity; a maintainer signs production releases with a private key)."""
from __future__ import annotations

import hashlib
import hmac
import json
from functools import lru_cache
from pathlib import Path

_KB_DIR = Path(__file__).resolve().parents[1].parent / "vendored_data" / "hazard_kb"
DEFAULT_KEY = b"biofirewall-hazard-kb-public-integrity-key-v1"   # public: integrity only. Production: private key.
_SIG_FIELDS = ("content_sha256", "hmac_sha256")


def _canonical(kb: dict) -> bytes:
    """Canonical bytes of the KB CONTENT (everything except the signature fields), stably ordered."""
    body = {k: v for k, v in kb.items() if k not in _SIG_FIELDS}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


def content_digest(kb: dict) -> str:
    return hashlib.sha256(_canonical(kb)).hexdigest()


def sign_kb(kb: dict, key: bytes = DEFAULT_KEY) -> str:
    return hmac.new(key, _canonical(kb), hashlib.sha256).hexdigest()


def verify_kb(kb: dict, key: bytes = DEFAULT_KEY) -> bool:
    """True iff the content digest AND the HMAC signature both match - a single edited entry breaks both."""
    ok_digest = hmac.compare_digest(kb.get("content_sha256", ""), content_digest(kb))
    ok_sig = hmac.compare_digest(kb.get("hmac_sha256", ""), sign_kb(kb, key))
    return ok_digest and ok_sig


def _versions() -> list[str]:
    if not _KB_DIR.exists():
        return []
    return sorted(p.stem for p in _KB_DIR.glob("*.yaml"))


def latest_version() -> str | None:
    v = _versions()
    return v[-1] if v else None


@lru_cache(maxsize=4)
def load_kb(version: str | None = None) -> dict:
    """Load a KB release (the latest by default). {} if none vendored."""
    import yaml
    version = version or latest_version()
    if not version:
        return {}
    return yaml.safe_load((_KB_DIR / f"{version}.yaml").read_text(encoding="utf-8"))


def entries(kb: dict | None = None, type: str | None = None) -> list[dict]:
    kb = kb if kb is not None else load_kb()
    es = kb.get("entries", [])
    return [e for e in es if type is None or e.get("type") == type]
