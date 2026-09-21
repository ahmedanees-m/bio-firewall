"""The signed design passport: what it binds, and that a verification helper always returns a verdict."""
from __future__ import annotations

import pytest

from bio_firewall.passport.sign import sign_passport, verify_passport


# --- a verification helper must return a verdict, never raise -------------------------------------------------
# A caller gates a downstream action on verify_passport(...). If a malformed signature raises instead of returning
# False, the failed check escapes the gate as a crash: synthesize() raises TypeError rather than GateBlocked and
# gated_cloudlab_submit raises despite contracting not to on a block.
@pytest.mark.parametrize("bad", [None, 123, ["sig"], {"sig": 1}, b"bytes", "ÿ" * 64])
def test_malformed_signature_is_false_not_an_exception(bad):
    p = sign_passport({"intent": "x"}, {"decision": "allow", "ruleset_version": "1", "evidence": []})
    assert verify_passport({**p, "signature": bad}) is False


@pytest.mark.parametrize("bad", [None, [], "passport", 7])
def test_non_dict_passport_is_false_not_an_exception(bad):
    assert verify_passport(bad) is False


def test_missing_signature_is_false():
    p = sign_passport({"intent": "x"}, {"decision": "allow", "ruleset_version": "1", "evidence": []})
    p.pop("signature")
    assert verify_passport(p) is False


# --- the passport binds the submitted artifact, not only the normalized plan -----------------------------------
def test_artifact_hash_binds_fields_outside_the_normalized_plan():
    """inputs_hash covers the five screened axes only, so without artifact_hash a passport minted for one design
    verifies against a materially different one (different vector, host, delivery)."""
    base = {"intent": "x", "sequence": "ATG"}
    swapped = {**base, "vector": "pX330", "host": "human", "delivery_detail": "AAV9"}
    p = sign_passport(base, {"decision": "allow", "ruleset_version": "1", "evidence": []}, artifact=base)
    q = sign_passport(base, {"decision": "allow", "ruleset_version": "1", "evidence": []}, artifact=swapped)
    assert p["inputs_hash"] == q["inputs_hash"]          # the normalized projection is identical
    assert p["artifact_hash"] != q["artifact_hash"]      # the submitted artifact is not
    assert verify_passport(p) and verify_passport(q)


def test_artifact_hash_is_covered_by_the_signature():
    base = {"intent": "x"}
    p = sign_passport(base, {"decision": "allow", "ruleset_version": "1", "evidence": []}, artifact=base)
    assert verify_passport({**p, "artifact_hash": "0" * 64}) is False      # cannot be swapped
    stripped = {k: v for k, v in p.items() if k != "artifact_hash"}
    assert verify_passport(stripped) is False                             # cannot be removed


def test_passport_without_artifact_stays_backward_compatible():
    """Omitting the artifact must leave the passport byte-identical to one minted before the field existed."""
    p = sign_passport({"intent": "x"}, {"decision": "allow", "ruleset_version": "1", "evidence": []})
    assert "artifact_hash" not in p
    assert verify_passport(p)


def test_dev_key_passport_is_refused_when_a_deployment_key_is_required(monkeypatch):
    """The marker is only a control if verification acts on it. Under
    BIOFW_REQUIRE_DEPLOYMENT_KEY every gate that calls verify_passport refuses a default-key
    passport, without each gate needing its own check."""
    monkeypatch.delenv("BIOFW_PASSPORT_KEY", raising=False)
    p = sign_passport({"intent": "x"}, {"decision": "allow", "ruleset_version": "1", "evidence": []})
    assert p.get("dev_key") is True
    assert verify_passport(p) is True                       # permissive by default
    monkeypatch.setenv("BIOFW_REQUIRE_DEPLOYMENT_KEY", "1")
    assert verify_passport(p) is False                      # refused when a real key is demanded


def test_requiring_a_deployment_key_does_not_reject_real_passports(monkeypatch):
    monkeypatch.setenv("BIOFW_PASSPORT_KEY", "a-real-deployment-key")
    monkeypatch.setenv("BIOFW_REQUIRE_DEPLOYMENT_KEY", "1")
    p = sign_passport({"intent": "x"}, {"decision": "allow", "ruleset_version": "1", "evidence": []})
    assert "dev_key" not in p
    assert verify_passport(p) is True
