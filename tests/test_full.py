"""Phase 1-3 acceptance: data-grounded locus axis, signed passport, tamper-evident audit, the per-axis
interception benchmark, and red-team robustness."""
from __future__ import annotations

from bio_firewall import screen
from bio_firewall.audit import AuditLog
from bio_firewall.data import gene_roles
from bio_firewall.eval import legitimate_research_not_blocked, reframing_resistance, run
from bio_firewall.passport import verify_passport


# ---- Axis 2 locus on real CC0 data (CancerMine/DepMap) ----
def test_locus_axis_uses_real_cancermine_depmap_data_when_vendored():
    roles = gene_roles("TP53")
    if not roles:                                    # vendored_data absent on a bare checkout -> skip
        return
    assert "TSG" in roles                            # TP53 is a tumour suppressor in CancerMine
    v = screen({"intent": "insert reporter", "gene": "TP53"})
    assert v["decision"] == "flag_for_review"        # TSG disruption flagged (not blocked)
    assert v["axes"]["locus"]["rule_id"] in ("locus.tumor_suppressor_disruption", "locus.genotoxic_proximity")
    assert v["axes"]["locus"]["extrapolating"] is True   # mechanism flag, not a validated cancer rate


# ---- P4 signed passport ----
def test_passport_is_signed_and_tamper_evident():
    v = screen({"intent": "therapeutic insert", "gene": "AAVS1"})
    p = v["passport"]
    assert verify_passport(p) is True
    p2 = dict(p)
    p2["decision"] = "refuse"                         # tamper
    assert verify_passport(p2) is False


# ---- P7 tamper-evident audit ----
def test_audit_log_chains_and_detects_tampering():
    log = AuditLog()
    for plan in ({"gene": "AAVS1"}, {"gene": "LMO2"}, {"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}):
        screen(plan, audit=log)
    assert len(log.entries) == 3 and log.verify() is True
    log.entries[0]["record"]["decision"] = "refuse"  # retroactive edit (the first plan decided 'allow')
    assert log.verify() is False


# ---- Section 7 per-axis interception benchmark ----
def test_benchmark_intercepts_what_homology_misses():
    r = run()
    assert r["homology_baseline_interception"] == 0.0     # homology screen is blind to structural hazards
    assert r["overall_interception"] >= 0.9               # the five-axis firewall catches them
    assert r["false_block_rate"] == 0.0                   # benign somatic plans are not blocked
    for axis in ("locus", "edit_type", "germline", "scale"):
        assert r["by_axis"][axis]["caught"] == r["by_axis"][axis]["n"]   # full interception per differentiating axis


# ---- P6 red-team ----
def test_reframing_does_not_flip_refuse_to_allow():
    assert reframing_resistance()["all_refused"] is True


def test_legitimate_research_is_flagged_not_blocked():
    assert legitimate_research_not_blocked()["none_blocked"] is True
