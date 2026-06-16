"""CI license gate (carried from PEN-STACK v6.6) — the vendored data is open-only (CC0/CC-BY/public-domain).
Fails the build if a restricted source (COSMIC, OncoKB) is the source of any vendored artifact, or a raw
restricted gene-list is committed. The legal crux: the oncogene/TSG *list* is from a CC0 compilation (CancerMine)."""
from __future__ import annotations

from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_VD = _ROOT / "vendored_data"


def test_data_licenses_manifest_exists_and_is_open_only():
    md = (_ROOT / "DATA_LICENSES.md").read_text(encoding="utf-8")
    assert "CancerMine" in md and "CC0" in md
    assert "open data only" in md.lower()
    assert "OncoKB" in md and "COSMIC" in md          # documented as restricted / not-vendored


def test_vendored_genotox_oracle_is_cancermine_not_cosmic_oncokb():
    p = _VD / "genotoxicity_oracle.yaml"
    if not p.exists():
        return                                         # vendored on a data-mounted build; skip on a bare checkout
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    onco = str(cfg.get("inputs", {}).get("oncogenes", "")).lower()
    assert "cancermine" in onco
    assert "cosmic" not in onco and "oncokb" not in onco


def test_no_restricted_source_in_committed_text():
    """No committed text artifact may carry an OncoKB/COSMIC export signature."""
    bad = []
    for p in _ROOT.rglob("*"):
        if p.suffix.lower() not in {".tsv", ".csv", ".yaml", ".yml", ".md", ".txt"}:
            continue
        if any(seg in str(p) for seg in (".git", "node_modules", "licensed_data", "site-packages")):
            continue
        if p.name == "DATA_LICENSES.md" or "test_data_licenses" in p.name:
            continue                                   # these legitimately *name* the restricted sources
        try:
            head = p.read_text(encoding="utf-8", errors="ignore")[:800]
        except Exception:  # noqa: BLE001
            continue
        if ("OncoKB Annotated" in head) or ("MSK-IMPACT" in head) or ("ROLE_IN_CANCER" in head and "GENOME_START" in head):
            bad.append(str(p.relative_to(_ROOT)))
    assert not bad, f"restricted gene-list signature in committed file(s): {bad}"
