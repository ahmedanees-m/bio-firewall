"""P4 - the signed design passport. Aggregates the verdict + an inputs hash into a tamper-evident, NTI/IBBIS-
aligned passport, HMAC-SHA256 signed with a deployment key (BIOFW_PASSPORT_KEY). A synthesis provider can verify
the passport to confirm a sequence was screened and what it was screened as."""
from __future__ import annotations

import hashlib
import hmac
import json
import os

_SCHEMA = "biofirewall/passport@1"


def _key() -> bytes:
    return os.getenv("BIOFW_PASSPORT_KEY", "biofirewall-dev-key-change-me").encode()


def _canonical(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


def sign_passport(plan: dict, verdict: dict, access: dict | None = None) -> dict:
    body = {
        "schema": _SCHEMA,
        "tools": ["bio-firewall"],
        "ruleset_version": verdict.get("ruleset_version"),
        "intent": plan.get("intent"),
        "inputs_hash": hashlib.sha256(_canonical(plan)).hexdigest(),
        "decision": verdict["decision"],
        "axes_triggered": [e["rule_id"] for e in verdict.get("evidence", [])],
    }
    # P9 (v0.8.0): bind the managed-access tier into the signed body so the resolution is tamper-evident. Omitted
    # when access is None, so a screen-only passport is byte-identical to the pre-v0.8 passport (backward compatible).
    if access is not None:
        body["access"] = {k: access[k] for k in ("legitimacy_level", "legitimacy_rank", "evidence_hash",
                                                  "required_legitimacy_rank", "resolution")}
    return {**body, "signature": hmac.new(_key(), _canonical(body), hashlib.sha256).hexdigest()}


def verify_passport(passport: dict) -> bool:
    """True iff the passport's HMAC matches its body (tamper-evident) under the current deployment key."""
    sig = passport.get("signature", "")
    body = {k: v for k, v in passport.items() if k != "signature"}
    expected = hmac.new(_key(), _canonical(body), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)
