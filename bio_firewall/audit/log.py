"""P7 - hash-chained audit log.

Each entry chains to the previous through a digest over (previous digest, record), so an entry that
is altered, reordered or removed from the middle breaks the chain.

Two limits are inherent to a bare hash chain and are stated here rather than left to be discovered:

  * Unkeyed, the chain protects against accidental corruption and against modification by a party
    who does not recompute it. Anyone able to write the store can recompute a self-consistent chain,
    because the digest needs no secret. Set BIOFW_AUDIT_KEY, or pass `key=`, to chain under HMAC so
    that recomputation requires the key.
  * A chain is self-consistent under truncation: any prefix verifies. Detecting a removed tail needs
    something retained outside the log, so `verify()` accepts the head digest and entry count that
    the caller recorded out of band. Without them, truncation is not detectable by the log alone.

`verify()` returns a verdict and never raises, since callers treat False as "do not trust this log".
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

_GENESIS = "0" * 64


def _key(explicit: str | bytes | None = None) -> bytes | None:
    """The audit key, if one is configured. None means an unkeyed chain."""
    k = explicit if explicit is not None else os.getenv("BIOFW_AUDIT_KEY")
    if not k:
        return None
    return k.encode() if isinstance(k, str) else k


def _hash(prev: str, record: dict, key: bytes | None = None) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    payload = (prev + body).encode()
    if key is None:
        return hashlib.sha256(payload).hexdigest()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


class AuditLog:
    """An append-only hash-chained log, optionally persisted as JSONL, one entry per line.

    `key`, or BIOFW_AUDIT_KEY, chains under HMAC instead of a bare digest. A keyed log cannot be
    recomputed without the key, which is what makes tampering detectable against an adversary who
    controls the store rather than only against accident.
    """

    def __init__(self, path: str | Path | None = None, key: str | bytes | None = None,
                 verify_on_load: bool = True):
        self.path = Path(path) if path else None
        self.key = _key(key)
        self.entries: list[dict] = []
        self.loaded_intact: bool | None = None
        if self.path and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        self.entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        self.loaded_intact = False
            # A log is otherwise extended without ever checking what it is being extended onto, so a
            # tampered file would silently acquire valid-looking new entries.
            if verify_on_load and self.loaded_intact is not False:
                self.loaded_intact = self.verify()

    @property
    def head(self) -> str:
        """The current chain head. Retain this out of band to detect a removed tail later."""
        return self.entries[-1]["hash"] if self.entries else _GENESIS

    @property
    def keyed(self) -> bool:
        return self.key is not None

    def append(self, record: dict) -> str:
        prev = self.head
        entry = {"prev": prev, "record": record, "hash": _hash(prev, record, self.key)}
        self.entries.append(entry)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        return entry["hash"]

    def verify(self, expected_head: str | None = None, expected_len: int | None = None) -> bool:
        """True iff the chain is internally consistent, and matches any anchor supplied.

        Internal consistency alone cannot detect a removed tail, because every prefix of a valid
        chain is itself valid. Pass `expected_head` or `expected_len`, retained outside the log, to
        detect truncation and tail forgery.
        """
        prev = _GENESIS
        for e in self.entries:
            if not isinstance(e, dict) or "record" not in e:
                return False
            if e.get("prev") != prev or e.get("hash") != _hash(prev, e["record"], self.key):
                return False
            prev = e["hash"]
        if expected_len is not None and len(self.entries) != expected_len:
            return False
        return not (expected_head is not None and prev != expected_head)
