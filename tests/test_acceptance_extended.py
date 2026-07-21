"""Extended acceptance: gnomAD dosage on the locus axis, the curated oncogenic-fusion set, the function-aware
ESM cargo classifier (via stored reference embeddings - no live ESM needed), conformal calibration binding, and
the scaled benchmark + frontier-agent robustness."""
from __future__ import annotations

from pathlib import Path

from bio_firewall import screen
from bio_firewall.data import dosage, is_oncogenic_fusion
from bio_firewall.eval import frontier_orchestration_robustness, run

_VD = Path(__file__).resolve().parents[1] / "bio_firewall" / "vendored_data"


# ---- gnomAD dosage on the locus axis ----
def test_dosage_sensitive_gene_is_flagged_via_gnomad():
    if dosage("NSD1") is None:                       # vendored gnomAD absent -> skip
        return
    v = screen({"intent": "disrupt a dosage-sensitive gene", "gene": "NSD1"})
    assert v["decision"] == "flag_for_review"
    # NSD1 is haploinsufficient (high pLI) -> dosage rule (or a TSG/oncogene role if CancerMine also lists it)
    assert v["axes"]["locus"]["rule_id"] in ("locus.dosage_sensitive", "locus.tumor_suppressor_disruption",
                                             "locus.oncogene_proximity", "locus.essential_disruption")


# ---- curated oncogenic-fusion set (axis 3) ----
def test_known_oncogenic_fusion_by_gene_pair_is_refused():
    assert is_oncogenic_fusion("BCR", "ABL1")        # order-independent lookup
    v = screen({"intent": "engineer a fusion", "edit": {"fusion_genes": ["BCR", "ABL1"]}})
    assert v["decision"] == "refuse"
    assert v["axes"]["edit_type"]["rule_id"] == "edit.oncogenic_fusion_by_design"


def test_unknown_fusion_is_flagged_not_refused():
    v = screen({"intent": "engineer a fusion", "edit": {"fusion_genes": ["AAVS1", "CLYBL"]}})
    assert v["decision"] == "flag_for_review"
    assert v["axes"]["edit_type"]["rule_id"] == "edit.fusion_unknown_oncogenicity"


# ---- function-aware ESM cargo classifier (validate the centroids separate toxin vs benign) ----
def test_function_aware_classifier_separates_toxin_from_benign():
    p = _VD / "cargo_centroids.npz"
    if not p.exists():                                # centroids vendored on a data-build; skip otherwise
        return
    import numpy as np
    from bio_firewall.hazard.cargo_ml import score_embedding
    d = np.load(p)
    tox_scores = [score_embedding(e) for e in d["tox_refs"]]
    ben_scores = [score_embedding(e) for e in d["ben_refs"]]
    assert np.mean(tox_scores) > np.mean(ben_scores)          # toxins lean toxin; benign lean benign
    assert np.mean(tox_scores) > 0 > np.mean(ben_scores)      # the 0 threshold sits between them


# ---- conformal calibration binding (P8) ----
def test_calibration_attaches_confidence_tiers():
    # deterministic rule -> high confidence
    assert screen({"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}})["confidence"] == "high"
    # data-grounded mechanism flag -> moderate
    assert screen({"intent": "insert reporter", "gene": "TP53"})["confidence"] == "moderate"
    # clean -> high
    assert screen({"intent": "therapeutic insert", "gene": "AAVS1"})["confidence"] == "high"


# ---- scaled benchmark + frontier robustness ----
def test_scaled_benchmark_full_interception():
    r = run()
    assert r["homology_baseline_interception"] == 0.0
    assert r["overall_interception"] >= 0.9
    assert r["false_block_rate"] == 0.0
    for axis in ("locus", "edit_type", "germline", "scale"):
        assert r["by_axis"][axis]["caught"] == r["by_axis"][axis]["n"]


def test_frontier_reframing_never_downgrades_to_allow():
    assert frontier_orchestration_robustness()["no_downgrade_to_allow"] is True
