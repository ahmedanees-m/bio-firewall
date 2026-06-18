"""Build (regenerate) a signed hazard-KB release from the in-code signatures + their provenance. Run after adding a
signature so the KB stays the single, versioned, provenanced source of record:

    python tools/build_hazard_kb.py 1.0.0 2026-06-18

Writes vendored_data/hazard_kb/<version>.yaml with per-entry provenance + a content digest + an HMAC signature.
A CI test (tests/test_kb.py) verifies the signature and that the KB is a SUPERSET of the in-code sets (consistency)."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bio_firewall.data import oncogenic_fusions                           # noqa: E402
from bio_firewall.eval.hazard_bench.oracles import TIER1_CLINICAL_CIS     # noqa: E402
from bio_firewall.hazard.edit_mech import IG_TCR_LOCI, KINASE_FUSION_GENES  # noqa: E402
from bio_firewall.hazard.locus import _GENOTOXIC_CIS                      # noqa: E402
from bio_firewall.kb.registry import content_digest, sign_kb             # noqa: E402


def build(kb_version: str, released: str) -> dict:
    entries: list[dict] = []
    for g in sorted(_GENOTOXIC_CIS):
        ctx, doi = TIER1_CLINICAL_CIS.get(g, ("genotoxic-CIS locus (insertional-oncogenesis literature)", None))
        entries.append({"id": f"CIS-{g}", "type": "genotoxic_cis_locus", "value": g,
                        "provenance": {"source": ctx, **({"doi": doi} if doi else {})}, "added_in": "0.3.0"})
    for key, rec in sorted(oncogenic_fusions().items()):
        entries.append({"id": "FUSION-" + key.replace("::", "-"), "type": "oncogenic_fusion_pair",
                        "value": sorted(key.split("::")),
                        "provenance": {"name": rec.get("name"), "cancer": rec.get("cancer"),
                                       "citation": rec.get("citation"), "source": "literature-curated canonical fusion"},
                        "added_in": "0.3.0"})
    for g in sorted(KINASE_FUSION_GENES):
        entries.append({"id": f"KINASE-{g}", "type": "fusion_kinase", "value": g,
                        "provenance": {"source": "recurrent fusion-kinase (function-family; public cancer-fusion biology)"},
                        "added_in": "0.6.0"})
    for loc in sorted(IG_TCR_LOCI):
        entries.append({"id": f"IGTCR-{loc.replace('@', '')}", "type": "ig_tcr_locus", "value": loc,
                        "provenance": {"source": "immunoglobulin / T-cell-receptor super-enhancer locus"},
                        "added_in": "0.6.0"})

    kb = {
        "kb_version": kb_version, "released": released, "schema_version": "1.0",
        "source_repo": "https://github.com/ahmedanees-m/bio-firewall",
        "note": "Signed, versioned hazard signatures (function/family/taxon-level; no hazard sequences). "
                "Contribute via docs/HAZARD_KB.md; regenerate with tools/build_hazard_kb.py.",
        "n_entries": len(entries), "entries": entries,
    }
    kb["content_sha256"] = content_digest(kb)
    kb["hmac_sha256"] = sign_kb(kb)
    return kb


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "1.0.0"
    released = sys.argv[2] if len(sys.argv) > 2 else "2026-06-18"
    out_dir = ROOT / "vendored_data" / "hazard_kb"
    out_dir.mkdir(parents=True, exist_ok=True)
    kb = build(version, released)
    (out_dir / f"{version}.yaml").write_text(yaml.safe_dump(kb, sort_keys=False), encoding="utf-8")
    print(f"wrote hazard-KB v{version}: {kb['n_entries']} entries | content_sha256 {kb['content_sha256'][:16]}...")
