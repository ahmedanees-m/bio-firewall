"""P4 - the signed design passport. Aggregates the verdict + an inputs hash into a tamper-evident, NTI/IBBIS-
aligned passport, HMAC-SHA256 signed with a deployment key (BIOFW_PASSPORT_KEY). A synthesis provider can verify
the passport to confirm a sequence was screened and what it was screened as."""
from __future__ import annotations

import hashlib
import hmac
import json
import os

_SCHEMA = "biofirewall/passport@1"


_DEV_KEY = "biofirewall-dev-key-change-me"


def _key() -> bytes:
    return os.getenv("BIOFW_PASSPORT_KEY", _DEV_KEY).encode()


def deployment_key_required() -> bool:
    """Whether this deployment refuses passports minted under the published default key.

    The `dev_key` marker is only a control if some party is obliged to act on it. Setting
    BIOFW_REQUIRE_DEPLOYMENT_KEY makes verification itself refuse such a passport, so every gate
    that already calls `verify_passport` enforces it without needing its own check."""
    return bool(os.getenv("BIOFW_REQUIRE_DEPLOYMENT_KEY"))


def using_dev_key() -> bool:
    """True when no deployment key is configured and the published default is in use.

    A passport signed under the published default is not authenticated: anyone holding the source
    can mint one. The fallback is retained so the package runs out of the box, but a passport minted
    under it says so in its signed body, so a verifier can refuse it rather than having to know how
    the issuer was configured."""
    return os.getenv("BIOFW_PASSPORT_KEY", _DEV_KEY) == _DEV_KEY


def _canonical(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


def sign_passport(plan: dict, verdict: dict, access: dict | None = None,
                  artifact: dict | None = None) -> dict:
    body = {
        "schema": _SCHEMA,
        "tools": ["bio-firewall"],
        "ruleset_version": verdict.get("ruleset_version"),
        "intent": plan.get("intent"),
        "inputs_hash": hashlib.sha256(_canonical(plan)).hexdigest(),
        "decision": verdict["decision"],
        "axes_triggered": [e["rule_id"] for e in verdict.get("evidence", [])],
    }
    # Signed, so it cannot be stripped or forged onto a passport: a verifier can tell an
    # unauthenticated development passport from a deployment one without out-of-band knowledge.
    if using_dev_key():
        body["dev_key"] = True
    # inputs_hash covers the normalized five-axis plan only, so anything the adapter does not map onto
    # an axis (vector, host, delivery detail, free-form fields) is unbound, and a passport minted for one
    # artifact verifies against a materially different one. Bind the submitted artifact as well. This is a
    # separate field rather than a change to inputs_hash, so passports minted earlier remain verifiable;
    # it sits inside the signed body, so it cannot be stripped from a passport that carried it.
    if artifact is not None:
        body["artifact_hash"] = hashlib.sha256(_canonical(artifact)).hexdigest()
    # P9: bind the managed-access tier into the signed body so the resolution is tamper-evident. Omitted
    # when access is None, so a screen-only passport is byte-identical to one without the access binding (backward compatible).
    if access is not None:
        body["access"] = {k: access[k] for k in ("legitimacy_level", "legitimacy_rank", "evidence_hash",
                                                  "required_legitimacy_rank", "resolution")}
    return {**body, "signature": hmac.new(_key(), _canonical(body), hashlib.sha256).hexdigest()}


def verify_passport(passport: dict) -> bool:
    """True iff the passport's HMAC matches its body (tamper-evident) under the current deployment key.

    Returns False for malformed input and never raises. Callers gate a downstream action on this result,
    so an exception here would convert a failed check into a crash: `synthesize` would raise TypeError
    instead of GateBlocked, and `gated_cloudlab_submit` would raise despite contracting not to on a block.
    A signature that is absent, not a string, or not ASCII is not a valid signature, so it is False.
    """
    if not isinstance(passport, dict):
        return False
    # A passport minted under the published default is unauthenticated. Where the deployment has
    # asked for a real key, refuse it here rather than leaving the marker for a caller to notice.
    if passport.get("dev_key") and deployment_key_required():
        return False
    sig = passport.get("signature")
    if not isinstance(sig, str):
        return False
    body = {k: v for k, v in passport.items() if k != "signature"}
    try:
        expected = hmac.new(_key(), _canonical(body), hashlib.sha256).hexdigest()
    except (TypeError, ValueError):          # a body that will not serialise is not a valid passport
        return False
    # Compared as bytes: compare_digest raises on a non-ASCII str, and a signature is always hex.
    return hmac.compare_digest(expected.encode("utf-8"), sig.encode("utf-8"))
