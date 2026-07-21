"""Regenerate the committed NIST-compatible benchmark export. Run after changing the export schema or the Tier-1 set:

    python tools/export_nist_benchmark.py

Writes standards/nist_benchmark_export.json. A CI test (tests/test_standards.py) validates it against the declared
schema and checks that export_benchmark() reproduces its content checksum (determinism)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bio_firewall.standards import export_benchmark, validate_export  # noqa: E402

if __name__ == "__main__":
    pkg = export_benchmark()
    report = validate_export(pkg)
    if not report["valid"]:
        raise SystemExit(f"export is invalid: {report['violations']}")
    out_dir = ROOT / "standards"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "nist_benchmark_export.json").write_text(json.dumps(pkg, indent=2, sort_keys=True), encoding="utf-8")
    print(f"wrote standards/nist_benchmark_export.json: {pkg['n_records']} records | "
          f"content_sha256 {pkg['content_sha256'][:16]}...")
