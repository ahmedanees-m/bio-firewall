"""P7 — tamper-evident, hash-chained audit log. Each entry chains to the previous via SHA256(prev_hash + record),
so any retroactive edit/deletion breaks the chain. Every screened plan + verdict is immutably logged + verifiable."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

_GENESIS = "0" * 64


def _hash(prev: str, record: dict) -> str:
    body = json.dumps(record, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256((prev + body).encode()).hexdigest()


class AuditLog:
    """An append-only hash-chained log. Optionally persisted as JSONL (one entry per line)."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.entries: list[dict] = []
        if self.path and self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.entries.append(json.loads(line))

    def append(self, record: dict) -> str:
        prev = self.entries[-1]["hash"] if self.entries else _GENESIS
        entry = {"prev": prev, "record": record, "hash": _hash(prev, record)}
        self.entries.append(entry)
        if self.path:
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        return entry["hash"]

    def verify(self) -> bool:
        """True iff the whole chain is intact (no entry was altered, reordered, or removed)."""
        prev = _GENESIS
        for e in self.entries:
            if e.get("prev") != prev or e.get("hash") != _hash(prev, e["record"]):
                return False
            prev = e["hash"]
        return True
