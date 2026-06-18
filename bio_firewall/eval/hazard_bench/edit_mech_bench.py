"""Benchmark 8 (v0.6.0) - WS-EDIT-MECH generalization. Does the de-novo mechanism screen flag known oncogenic
fusions that are ABSENT from the curated gene-pair list, with a controlled false-positive on benign constructs?

De-circularization: the curated list is `vendored_data/oncogenic_fusions.yaml` (14 canonical pairs). The held-out
oncogenic label is **COSMIC's TRANSLOCATION_PARTNER** pairs (local-only, never committed) - pairs the firewall's
mechanism rules (a CC0 fusion-kinase family + CancerMine roles) do NOT enumerate. A high recall = generalization.

Benign false-positive control: random pairs of NON-cancer, non-kinase genes (gnomAD universe) - a benign research
construct that must NOT trip the oncogenic-mechanism flag. (Caveat: a research fusion of a real oncogene
legitimately flags; the FP control is therefore non-cancer pairs, the construct that should be allowed.)"""
from __future__ import annotations

import random

from bio_firewall.data import _dosage, gene_roles, oncogenic_fusions
from bio_firewall.hazard.edit_mech import KINASE_FUSION_GENES, oncogenic_fusion_mechanism
from bio_firewall.eval.hazard_bench import oracles

SEED = 1234


def _boot_ci(flags, reps=2000, seed=7):
    if not flags:
        return [0.0, 0.0]
    rng = random.Random(seed)
    n = len(flags)
    means = sorted(sum(flags[rng.randrange(n)] for _ in range(n)) / n for _ in range(reps))
    return [round(means[int(0.025 * reps)], 3), round(means[int(0.975 * reps)], 3)]


def run(seed: int = SEED, n_benign: int = 400) -> dict:
    curated = {tuple(sorted(k.split("::"))) for k in oncogenic_fusions()}
    heldout = [p for p in oracles.cosmic_fusion_pairs() if p not in curated]
    if not heldout:
        return {"error": "COSMIC fusion pairs not mounted (BF_BENCH_ORACLES) - generalization benchmark skipped"}

    flagged = [int(oncogenic_fusion_mechanism(a, b)[0]) for a, b in heldout]
    kin = [(a, b) for a, b in heldout if a in KINASE_FUSION_GENES or b in KINASE_FUSION_GENES]
    kin_flagged = [int(oncogenic_fusion_mechanism(a, b)[0]) for a, b in kin]

    # benign control: pairs of non-cancer, non-kinase, non-IG genes
    universe = [g for g in _dosage() if not gene_roles(g) and g not in KINASE_FUSION_GENES]
    rng = random.Random(seed)
    benign = [(rng.choice(universe), rng.choice(universe)) for _ in range(n_benign)]
    fp = [int(oncogenic_fusion_mechanism(a, b)[0]) for a, b in benign]

    return {
        "n_curated_pairs": len(curated),
        "n_heldout_cosmic_pairs": len(heldout),
        "mechanism_recall_on_heldout": round(sum(flagged) / len(flagged), 3),
        "mechanism_recall_CI": _boot_ci(flagged),
        "kinase_subset": {"n": len(kin), "recall": round(sum(kin_flagged) / len(kin_flagged), 3) if kin else None},
        "benign_false_positive_rate": round(sum(fp) / len(fp), 3),
        "benign_fp_CI": _boot_ci(fp),
        "gate_pass": bool(_boot_ci(flagged)[0] > 0.0 and _boot_ci(fp)[1] < 0.20),
        "gate": "generalization recall CI lower-bound > 0 AND benign-FP CI upper-bound < 0.20",
        "note": "COSMIC fusion genes overlap CancerMine oncogene roles, so recall is partly role-driven; the "
                       "kinase-family subset is the cleaner generalization signal (a CC0 family list, not COSMIC). A "
                       "research fusion of a real oncogene legitimately flags - the FP control is non-cancer pairs.",
        "seed": seed,
    }
