"""WS-STRUCT (v0.6.0) - the 3-signal ensemble + abstain-on-disagreement math. Synthetic, no Foldseek/torch; the
AlphaFold-DB + Foldseek run is on the VM (struct_bench via run_struct_vm)."""
from __future__ import annotations

import numpy as np

from bio_firewall.hazard.struct_channel import abstain_mask, ensemble_score, normalize01, tpr_at_fpr


def test_normalize01_range():
    n = normalize01([1.0, 2.0, 3.0, 5.0])
    assert n.min() == 0.0 and n.max() == 1.0


def test_ensemble_ranks_when_signals_agree():
    esm = np.array([0.1, 0.2, 0.8, 0.9])
    struct = np.array([10.0, 20.0, 300.0, 400.0])      # different scale, same ordering
    e = ensemble_score(esm, struct)
    assert e[3] > e[0] and e[2] > e[1]                 # ensemble preserves the shared ranking


def test_abstain_on_strong_disagreement():
    esm = np.array([0.95, 0.5, 0.05])                  # toxin / mid / benign
    struct = np.array([1.0, 50.0, 100.0])              # benign / mid / toxin  (normalized: 0 / .49 / 1)
    a = abstain_mask(esm, struct)
    assert a[0] and a[2]                               # the two ends strongly disagree -> abstain
    assert not a[1]                                    # the middle agrees-ish -> no abstain


def test_tpr_at_fpr_perfect():
    assert tpr_at_fpr([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0
