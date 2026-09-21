#!/usr/bin/env python3
"""Per-channel ablation of the locus axis on the held-out CCGD drivers.

The held-out analysis establishes that the axis enriches for outcome-defined drivers it did not
learn from the curated cancer list. It does not establish which remaining channel carries that
signal. The manuscript attributes it to dosage sensitivity and essentiality; this measures it.

Three channels can fire on a held-out gene: the clinical common-insertion-site list, DepMap
essentiality, and gnomAD dosage sensitivity. Each is disabled in turn at the point the locus rules
read it, and the held-out enrichment is recomputed. A channel that carries signal will lower AUROC
and the odds ratio when removed; a channel that carries none will leave them unchanged.

Leave-one-out isolates each channel's marginal contribution given the others. Leave-one-in is also
reported, because the channels overlap and a marginal contribution can be small while the channel
still carries the signal on its own.

Reuses the frozen scorer, universe and gate from locus_mouse_outcome_validation, so the baseline row
reproduces the committed result rather than approximating it.
"""
from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from pathlib import Path

import bio_firewall.hazard.locus as L
import locus_mouse_outcome_validation as lv
from bio_firewall.eval.hazard_bench.locus_outcome import validate_enrichment

CHANNELS = ("cis_list", "depmap_essential", "gnomad_dosage")


@contextmanager
def channels(enabled: set[str]):
    """Run with only `enabled` channels visible to the locus rules.

    Patched where the rules read, not where the data is stored, so the rule order and every other
    axis behave exactly as in the frozen run."""
    orig_cis, orig_roles, orig_dosage = L._GENOTOXIC_CIS, L.gene_roles, L.dosage
    try:
        if "cis_list" not in enabled:
            L._GENOTOXIC_CIS = frozenset()
        if "depmap_essential" not in enabled:
            # Strip only essentiality. Cancer roles are already absent on the held-out subset by
            # construction, and removing them here would change which genes are held out.
            L.gene_roles = lambda g: {r for r in orig_roles(g) if r.lower() != "essential"}
        if "gnomad_dosage" not in enabled:
            L.dosage = lambda g: None
        yield
    finally:
        L._GENOTOXIC_CIS, L.gene_roles, L.dosage = orig_cis, orig_roles, orig_dosage


def held_out_enrichment(universe, positives) -> dict:
    """The held-out (non-CancerMine) enrichment under whatever channel patching is in force."""
    pos = {g.upper() for g in positives}
    rows = [(g, *lv.score_gene(g), int(g in pos)) for g in universe if lv.is_held_out(g)]
    res = validate_enrichment(risk=[r[1] for r in rows], flag=[r[2] for r in rows],
                              outcome=[r[3] for r in rows], clusters=[r[0] for r in rows])
    res["n_genes"] = len(rows)
    res["n_positives"] = int(sum(r[3] for r in rows))
    res["n_flagged"] = int(sum(r[2] for r in rows))
    res["n_flagged_positives"] = int(sum(1 for r in rows if r[2] == 1 and r[3] == 1))
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--positives", default="data/locus_outcome_inputs/ccgd_recurrent.txt")
    ap.add_argument("--out", default="results/locus_channel_ablation.json")
    a = ap.parse_args()

    positives = [ln.strip().upper() for ln in Path(a.positives).read_text().splitlines() if ln.strip()]
    universe = sorted(set(lv.build_universe()) | set(positives))

    conditions = [("all_channels", set(CHANNELS))]
    conditions += [(f"minus_{c}", set(CHANNELS) - {c}) for c in CHANNELS]
    conditions += [(f"only_{c}", {c}) for c in CHANNELS]
    conditions += [("no_channels", set())]

    out = {
        "design": ("held-out CCGD drivers, non-CancerMine subset; each channel disabled where the "
                   "locus rules read it; gene-clustered bootstrap as in the frozen run"),
        "positives_file": a.positives,
        "n_universe": len(universe),
        "conditions": {},
    }
    for name, enabled in conditions:
        with channels(enabled):
            res = held_out_enrichment(universe, positives)
        out["conditions"][name] = res
        print(f"{name:26s} n={res['n_genes']:6d} pos={res['n_positives']:5d} "
              f"flagged={res['n_flagged']:5d}  AUROC={res.get('AUROC')} CI={res.get('AUROC_CI')} "
              f"OR={res.get('odds_ratio')} CI={res.get('odds_ratio_CI')}", flush=True)

    base = out["conditions"]["all_channels"]
    out["marginal_contribution"] = {
        c: {
            "delta_AUROC_when_removed": round(
                (out["conditions"][f"minus_{c}"].get("AUROC") or 0) - (base.get("AUROC") or 0), 4),
            "delta_odds_ratio_when_removed": round(
                (out["conditions"][f"minus_{c}"].get("odds_ratio") or 0) - (base.get("odds_ratio") or 0), 4),
            "AUROC_alone": out["conditions"][f"only_{c}"].get("AUROC"),
            "odds_ratio_alone": out["conditions"][f"only_{c}"].get("odds_ratio"),
            "flagged_positives_alone": out["conditions"][f"only_{c}"].get("n_flagged_positives"),
        }
        for c in CHANNELS
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2))
    print("\nmarginal contribution:")
    print(json.dumps(out["marginal_contribution"], indent=1))
    print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()
