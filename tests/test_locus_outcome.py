"""WS-LOCUS-OUTCOME (v0.5.0) — the generic enrichment harness (OR/AUROC + gene-clustered bootstrap). Synthetic
data, no VISDB/pandas; the real VISDB open-data floor (run_visdb) runs on the VM."""
from __future__ import annotations

import numpy as np

from bio_firewall.eval.hazard_bench.locus_outcome import _auroc, _odds_ratio, validate_enrichment


def test_odds_ratio_detects_and_nulls():
    flag = [1, 1, 1, 1, 0, 0, 0, 0]
    assert _odds_ratio(flag, [1, 1, 1, 0, 0, 0, 0, 1]) > 3      # flagged co-occur with outcome
    assert 0.3 < _odds_ratio(flag, [1, 0, 1, 0, 1, 0, 1, 0]) < 3   # no association -> ~1


def test_auroc_separates():
    assert _auroc([0, 0, 0, 1, 1, 1], [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]) == 1.0


def test_validate_enrichment_passes_on_real_signal_and_fails_on_null():
    rng = np.random.RandomState(0)
    # 40 genes; "flagged" genes (risk high) carry tumor sites more often -> enrichment present
    genes = [f"G{i}" for i in range(40)]
    risk, flag, outcome, clusters = [], [], [], []
    for i, g in enumerate(genes):
        hi = i < 20
        for _ in range(rng.randint(5, 15)):                     # many sites per gene -> clustering matters
            risk.append(0.5 + 0.3 * rng.rand() if hi else 0.1 * rng.rand())
            flag.append(1 if hi else 0)
            outcome.append(int(rng.rand() < (0.6 if hi else 0.2)))
            clusters.append(g)
    r = validate_enrichment(risk, flag, outcome, clusters)
    assert r["gate_pass"] is True
    assert r["AUROC"] > 0.5 and r["odds_ratio"] > 1

    # null: outcome independent of flag -> gate should NOT pass
    out_null = [int(rng.rand() < 0.4) for _ in outcome]
    rn = validate_enrichment(risk, flag, out_null, clusters)
    assert rn["gate_pass"] is False
