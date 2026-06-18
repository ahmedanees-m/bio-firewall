#!/usr/bin/env python3
"""WS-LOCUS-MOUSE-OUTCOME (v0.9.0) - outcome-validate the BioFirewall locus axis against REAL in vivo
insertional-oncogenesis outcomes (mouse transposon forward-genetic screens), with an explicit circularity control.

WHY (the gap this closes):
  The locus axis flags on MECHANISM; the two gene-census benchmarks (Cancer Gene Census 80.4%, OncoKB 82.0%) are
  recall-against-curation. The open human integration-site catalogue (VISDB) was the WRONG biology (~96% HTLV,
  viral-oncoprotein-driven; AUROC ~0.449). Mouse transposon forward-genetic screens define cancer drivers by
  *causing tumors when insertionally mutated in vivo* - a real OUTCOME anchor on the RIGHT (insertion-site-driven)
  biology, conserved with the gammaretroviral/lentiviral vector mechanism the axis models.

DATA (open; verified live 2026-06-19):
  CCGD - Candidate Cancer Gene Database (Abbott et al. 2015, Nucleic Acids Research 43(D1):D844-D848,
  doi:10.1093/nar/gku770, PMID 25190456; http://ccgd-starrlab.oit.umn.edu/). Positives = human-ortholog driver
  symbols, derived from the live export (data/locus_outcome_inputs/, see SOURCE.txt). RTCGD (Akagi et al. 2004,
  NAR 32:D523, doi:10.1093/nar/gkh013) is the retroviral-screen cross-check.

THE CIRCULARITY CONTROL (the crux):
  The axis already knows oncogenes/TSGs from CancerMine. Testing genes that are ALSO in CancerMine is partly
  circular, so we report TWO results:
    (A) ALL drivers   - operational enrichment (axis may use its full knowledge).
    (B) HELD-OUT drivers NOT in the axis's CancerMine roles - the NON-CIRCULAR test: the axis can only fire via
        DepMap-essentiality / gnomAD-dosage / the 12-gene clinical-CIS list. (B) is the load-bearing result.

PRE-REGISTERED ACCEPTANCE (prereg/ws_locus_mouse_outcome.yaml, SHA-locked before the run; honest-failure pre-committed):
  PASS iff, on held-out (B), the locus risk is enriched for outcome-defined drivers: AUROC bootstrap CI excluding
  0.5 OR odds-ratio CI excluding 1. HONEST-FAILURE: if (B) fails, report it; the axis's outcome signal is then
  confined to its curated list (a real limit). Do NOT tune the gene sets or thresholds to rescue (B).

CAVEATS (carried verbatim into the manuscript):
  - Mouse, not human (species gap) - but the tumor-prone mouse model is the field's PRECLINICAL standard for vector
    genotoxicity (cf. Montini et al.). State it; do not hide it.
  - Gene-level; the event-level POSITIONAL score (TSS/enhancer distance) needs coordinate-level data with clonality
    (some Sleeping Beauty datasets carry it) - declared next step.

USAGE (from the repo root):
  python locus_mouse_outcome_validation.py --selftest
  python locus_mouse_outcome_validation.py --positives data/locus_outcome_inputs/ccgd_recurrent.txt \
         --out results/locus_mouse_outcome.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bio_firewall
from bio_firewall.data import dosage, gene_roles
from bio_firewall.eval.hazard_bench.locus_outcome import validate_enrichment
from bio_firewall.hazard.locus import _GENOTOXIC_CIS, screen_locus

_REPO_ROOT = Path(bio_firewall.__file__).resolve().parent.parent      # robust: repo root holds vendored_data/
_CANCERMINE_ROLES = {"oncogene", "tsg", "driver"}                     # the axis's curated cancer knowledge

# Graded risk per finding rule (monotone in severity; continuous-enough for AUROC).
_RULE_RISK = {
    "locus.oncogene_activation_by_design": 1.00,
    "locus.genotoxic_proximity": 0.90,
    "locus.tumor_suppressor_disruption": 0.70,
    "locus.oncogene_proximity": 0.70,
    "locus.essential_disruption": 0.60,
    "locus.dosage_sensitive": 0.50,
    "locus.positional_oncogene_promoter": 0.50,
    "locus.positional_oncogene_enhancer": 0.50,
}


def score_gene(symbol: str) -> tuple[float, int]:
    """(risk in [0,1], flag in {0,1}) for a gene-level plan at this locus. Reads the Finding's `decision` field
    (NOT `severity` - that field does not exist on Finding; reading it returns null and silently zeros every score)."""
    f = screen_locus({"locus": {"gene": symbol}})
    dec = getattr(f, "decision", None) or (f.get("decision") if isinstance(f, dict) else None)
    rule = getattr(f, "rule_id", None) or (f.get("rule_id") if isinstance(f, dict) else None)
    if dec in (None, "clear", "clean"):
        return 0.0, 0
    return _RULE_RISK.get(rule, 0.4), 1


def is_held_out(symbol: str) -> bool:
    """True if the axis did NOT get this gene's cancer role from CancerMine (the non-circular subset)."""
    return not (_CANCERMINE_ROLES & {r.lower() for r in gene_roles(symbol)})


def build_universe() -> list[str]:
    """Background gene universe = the axis's own gene table (CancerMine + DepMap + gnomAD symbols)."""
    import pandas as pd
    vd = _REPO_ROOT / "vendored_data"
    genes: set[str] = set()
    for fn, col in (("locus_genes.parquet", "gene"), ("gnomad_constraint.parquet", "gene")):
        p = vd / fn
        if p.exists():
            genes.update(pd.read_parquet(p)[col].astype(str).str.upper())
    genes.update(_GENOTOXIC_CIS)
    return sorted(genes)


def run(positives: list[str], universe: list[str]) -> dict:
    pos = {g.upper() for g in positives}
    universe_set = set(universe) | pos                       # ensure positives are scoreable
    rows = [(g, *score_gene(g), int(g in pos), is_held_out(g)) for g in sorted(universe_set)]

    def _subset(held_only: bool) -> dict:
        sub = [r for r in rows if (r[4] if held_only else True)]
        res = validate_enrichment(risk=[r[1] for r in sub], flag=[r[2] for r in sub],
                                  outcome=[r[3] for r in sub], clusters=[r[0] for r in sub])
        res["n_positives"] = int(sum(r[3] for r in sub))
        return res

    held_pos = [r for r in rows if r[3] == 1 and r[4]]
    decomp = {"held_out_positives": len(held_pos),
              "via_CIS_list": sum(1 for r in held_pos if r[0] in _GENOTOXIC_CIS),
              "via_depmap_essential": sum(1 for r in held_pos if "essential" in {x.lower() for x in gene_roles(r[0])}),
              "via_gnomad_dosage": sum(1 for r in held_pos if (dosage(r[0]) or (0,))[0] and dosage(r[0])[0] >= 0.9),
              "flagged_any": sum(1 for r in held_pos if r[2] == 1)}

    return {
        "n_universe": len(universe_set),
        "A_all_drivers": _subset(held_only=False),           # operational (secondary)
        "B_heldout_non_cancermine": _subset(held_only=True),  # NON-CIRCULAR - the pre-registered gate
        "held_out_feature_decomposition": decomp,
        "note": "Gate is on B (AUROC CI excludes 0.5 OR OR CI excludes 1). A and the decomposition are reported, "
                "not gated. Mouse preclinical model; species gap stated as a limitation.",
    }


def _selftest() -> None:
    """Prove the pipeline runs end-to-end on a tiny illustrative set (NOT a validation result)."""
    out = run(["LMO2", "MECOM", "CCND1", "FOXP1", "PIK3CA"], build_universe())
    print(json.dumps({"SELFTEST_ONLY_not_a_result": True, "n_universe": out["n_universe"],
                      "B_AUROC": out["B_heldout_non_cancermine"].get("AUROC"),
                      "decomp": out["held_out_feature_decomposition"]}, indent=2))
    print("\nPipeline OK. Run with --positives data/locus_outcome_inputs/ccgd_recurrent.txt.", file=sys.stderr)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--positives", help="file: one HUMAN-ortholog gene symbol per line (CCGD drivers)")
    ap.add_argument("--out", default="results/locus_mouse_outcome.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.positives:
        _selftest()
        return
    positives = [ln.strip().upper() for ln in Path(a.positives).read_text().splitlines() if ln.strip()]
    out = run(positives, build_universe())
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2))
    b = out["B_heldout_non_cancermine"]
    print(f"[GATE] held-out AUROC={b.get('AUROC')} CI={b.get('AUROC_CI')} | "
          f"OR={b.get('odds_ratio')} CI={b.get('odds_ratio_CI')} | "
          f"PASS={b.get('gate_pass')}  (n_pos_heldout={b.get('n_positives')})", file=sys.stderr)


if __name__ == "__main__":
    main()
