"""WS-DECOMP (v0.5.0) - the session-level decomposition aggregator catches hazards split across calls that each
pass the per-artifact screen. Deterministic, no torch/esm/COSMIC needed."""
from __future__ import annotations

from bio_firewall import screen
from bio_firewall.intercept.session import SessionMonitor, reassemble

_LINK1 = "ACGTACGTACGTACGTACGT"      # 20-bp Gibson junctions
_LINK2 = "TTGGCCAATTGGCCAATTGG"


def test_cumulative_scale_caught_when_each_call_passes():
    """26 calls each deleting 45 kb: each is < the 50 kb edit-axis threshold (per-artifact clear), but the session
    restructures ~1.17 Mb - only the cross-call aggregate trips the scale axis."""
    sm = SessionMonitor("s1")
    for _ in range(26):
        plan = {"intent": "research deletion tiling", "edit": {"deleted_bp": 45_000}}
        v = screen(plan)
        assert v["decision"] == "allow"                  # each call individually passes
        sm.observe(plan, v)
    agg = sm.aggregate()
    assert agg["decision"] == "flag_for_review"
    assert any(s.startswith("session.") for s in agg["decomposition_signals"])


def test_fragment_assembly_reconstructed_across_calls():
    f1 = "AAAACCCCGGGGTTTTACGT" + _LINK1
    f2 = _LINK1 + "GGGGCCCCAAAATTTTACGT" + _LINK2
    f3 = _LINK2 + "TTTTGGGGCCCCAAAAACGT"
    chains = reassemble([f1, f2, f3])
    assert any(c["n_fragments"] == 3 for c in chains)    # the three fragments form one assembly chain

    sm = SessionMonitor("s2")
    for f in (f1, f2, f3):
        plan = {"intent": "insert a benign fragment", "cargo": {"sequence": f, "function": "spacer"}}
        sm.observe(plan, screen(plan))
    agg = sm.aggregate()
    assert agg["decision"] in ("flag_for_review", "refuse")
    assert "session.covert_multifragment_assembly" in agg["decomposition_signals"]


def test_coordinated_genotoxic_loci_flagged():
    sm = SessionMonitor("s3")
    for g in ("LMO2", "MECOM", "EVI1"):                  # three distinct clinical-CIS loci, separate calls
        plan = {"intent": "insert reporter", "gene": g, "cell_type": "hspc"}
        sm.observe(plan, screen(plan))
    agg = sm.aggregate()
    assert "session.coordinated_oncogenic_loci" in agg["decomposition_signals"]


def test_benign_multicall_session_is_not_flagged():
    sm = SessionMonitor("s4")
    for _ in range(3):
        plan = {"intent": "insert a small reporter", "edit": {"inserted_bp": 1_200}}
        sm.observe(plan, screen(plan))
    agg = sm.aggregate()
    assert agg["decision"] == "allow"
    assert agg["decomposition_signals"] == []


def test_reassemble_ignores_unrelated_fragments():
    assert reassemble(["AAAAAAAAAAAAAAAAAAAAAA", "CCCCCCCCCCCCCCCCCCCCCC"]) == []   # no shared junction
