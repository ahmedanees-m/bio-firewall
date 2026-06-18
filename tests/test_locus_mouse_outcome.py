"""WS-LOCUS-MOUSE-OUTCOME (v0.9.0): the locus scorer reads the correct Finding field (a regression guard on the
decision-vs-severity bug that zeroed every score), the held-out (non-circular) logic is correct, and the committed
CCGD-derived inputs + the frozen result are internally consistent and clear the pre-registered gate."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
import locus_mouse_outcome_validation as lv  # noqa: E402


def test_scorer_reads_decision_not_severity():
    risk, flag = lv.score_gene("LMO2")                 # clinical-CIS locus -> genotoxic_proximity rule
    assert flag == 1 and risk == 0.9                   # reading the nonexistent `severity` field would zero this
    assert lv.score_gene("ZZZNOTAGENE")[1] == 0        # unknown symbol -> clear


def test_held_out_logic_is_non_circular():
    assert lv.is_held_out("MYC") is False              # canonical CancerMine oncogene -> circular, excluded from (B)
    assert lv.is_held_out("ZZZNOTAGENE") is True       # no curated cancer role -> held-out (signal beyond the list)


def test_committed_inputs_counts_and_cleaning():
    inp = _ROOT / "data" / "locus_outcome_inputs"
    allg = [g.strip() for g in (inp / "ccgd_all.txt").read_text().splitlines() if g.strip()]
    rec = [g.strip() for g in (inp / "ccgd_recurrent.txt").read_text().splitlines() if g.strip()]
    assert len(allg) == 9219 and len(rec) == 4689      # the re-derived positive-set counts
    assert set(rec) <= set(allg)                       # recurrent is a subset of all
    assert "DECR1" in set(allg)                        # a real gene wrongly matched by a naive date-regex is retained
    assert not any(g.upper() in {"1-MAR", "2-SEP", "9-SEP"} for g in allg)   # Excel artifacts removed


def test_committed_result_passes_gate_and_is_consistent():
    res = json.loads((_ROOT / "results" / "locus_mouse_outcome.json").read_text())
    b = res["B_heldout_non_cancermine"]
    assert b["gate_pass"] is True
    assert b["AUROC_CI"][0] > 0.5 or b["odds_ratio_CI"][0] > 1.0          # the pre-registered gate
    assert b["n_positives"] == 3625
    assert abs(b["AUROC"] - 0.605) < 0.01 and abs(b["odds_ratio"] - 3.34) < 0.05
    d = res["held_out_feature_decomposition"]
    assert d["via_CIS_list"] == 0                                          # held-out -> never via the curated CIS list
    assert max(d["via_depmap_essential"], d["via_gnomad_dosage"]) <= d["flagged_any"] <= \
        d["via_depmap_essential"] + d["via_gnomad_dosage"]                 # overlap allowed (essential AND dosage)
