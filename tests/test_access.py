"""The managed/tiered access plane (P9) - a deterministic (verdict x tier) resolution, bound
tamper-evidently into the passport (P4) + audit (P7), plus the one-call managed entry point. CI-safe (the cargo axis
degrades gracefully without the PEN-STACK Guardian)."""
from __future__ import annotations

import pytest

from bio_firewall import screen
from bio_firewall.access import LEGITIMACY, RESOLUTIONS, apply_access, resolve, screen_managed, verify_access
from bio_firewall.adapters.generic_artifact import normalize
from bio_firewall.audit.log import AuditLog

_FLAG = {"intent": "knock-in study", "gene": "LMO2", "cell_type": "hspc"}                 # locus -> flag_for_review
_REFUSE = {"intent": "clinical embryo edit", "gene": "CCR5",
           "germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}     # germline -> refuse
_ALLOW = {"intent": "insert a therapeutic FIX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"}


# --- the pre-registered (verdict x tier) matrix: resolve() is total + deterministic ---
def test_resolve_matrix_is_total_and_as_specified():
    for lvl in LEGITIMACY.values():                                   # refuse is never unlocked by any tier
        assert resolve("refuse", lvl) == "refused"
        assert resolve("refuse", lvl, low_confidence=True) == "refused"
    assert resolve("flag_for_review", LEGITIMACY["unverified"]) == "held_pending"
    assert resolve("flag_for_review", LEGITIMACY["declared"]) == "held_pending"
    assert resolve("flag_for_review", LEGITIMACY["verified"]) == "released_with_review"
    assert resolve("flag_for_review", LEGITIMACY["credentialed"]) == "released_with_review"
    for lvl in LEGITIMACY.values():                                   # a confident allow releases at every tier
        assert resolve("allow", lvl) == "released"
    assert resolve("allow", LEGITIMACY["unverified"], low_confidence=True) == "held_pending"     # out-of-KB escalates
    assert resolve("allow", LEGITIMACY["verified"], low_confidence=True) == "released_with_review"
    for d in ("allow", "flag_for_review", "refuse"):                  # totality + closed resolution set
        for lvl in LEGITIMACY.values():
            for lc in (False, True):
                assert resolve(d, lvl, low_confidence=lc) in RESOLUTIONS


def test_resolution_is_deterministic():
    assert resolve("flag_for_review", LEGITIMACY["verified"]) == resolve("flag_for_review", LEGITIMACY["verified"])


def test_flag_resolves_by_legitimacy_and_binds_passport():
    v = screen(_FLAG)
    assert v["decision"] == "flag_for_review"
    plan = normalize(_FLAG)
    unv = apply_access(v, plan, legitimacy="unverified")
    ver = apply_access(v, plan, legitimacy="credentialed",
                       evidence={"affiliation": "Uni X", "purpose": "gene-therapy safety study"},
                       verification_hook="institutional_sso")
    assert unv["resolution"] == "held_pending"
    assert ver["resolution"] == "released_with_review"
    assert verify_access(unv) and verify_access(ver)
    assert unv["passport"]["access"]["legitimacy_level"] == "unverified"          # tier bound into the passport
    assert unv["passport"]["decision"] == "flag_for_review"                       # verdict-consistent


def test_tier_gating_is_tamper_evident():
    v = screen(_FLAG)
    acc = apply_access(v, normalize(_FLAG), legitimacy="unverified")
    assert verify_access(acc)
    acc["passport"]["access"]["resolution"] = "released"                          # mutate the bound resolution
    assert not verify_access(acc)                                                 # signature breaks


def test_audit_logs_tier_and_evidence_and_chain_holds():
    log = AuditLog()
    v = screen_managed(_FLAG, legitimacy="verified", evidence={"affiliation": "Lab Y"},
                       verification_hook="orcid", audit=log)
    assert v["access"]["resolution"] == "released_with_review"
    assert log.verify()                                                           # screen + access entries chained
    ev = [e["record"] for e in log.entries if e["record"].get("event") == "access_resolution"]
    assert ev and ev[0]["legitimacy_level"] == "verified"
    assert ev[0]["evidence_hash"] == v["access"]["evidence_hash"]


def test_refuse_never_unlocked_even_for_credentialed():
    v = screen_managed(_REFUSE, legitimacy="credentialed", evidence={"affiliation": "anything"},
                       verification_hook="kyc")
    assert v["decision"] == "refuse" and v["access"]["resolution"] == "refused"


def test_credentialing_authority_is_integration_point_not_operational():
    v = screen_managed(_ALLOW, legitimacy="declared")
    assert v["access"]["credentialing_authority"] == "integration_point"


def test_unknown_legitimacy_rejected():
    v = screen(_FLAG)
    with pytest.raises(ValueError):
        apply_access(v, normalize(_FLAG), legitimacy="trust-me")


def test_screen_only_passport_is_backward_compatible():
    v = screen(_ALLOW)
    assert "access" not in v["passport"]                                          # no access block without P9
