"""Gate the PEN-STACK cloud-lab execution bridge.

PEN-STACK exposes a design->physical-execution path: `pen_stack.build.cloudlab.submit(design, experiment, ...)`
(raises `ProtocolExportError` when its own in-design gate blocks) and `submit_gated(...)` (returns a structured
refusal). PEN-STACK's own gate is the necessary-not-sufficient in-design screen; BioFirewall is the
comprehensive downstream screen. No physical submission should proceed without a verified BioFirewall `allow` passport
that MATCHES the design - and BioFirewall runs FIRST, in-workflow, so an agent cannot route around it.

The interception contract (what the tests assert):
  - allow  : the design is submitted, carrying the BioFirewall passport; pen-stack's own gate still runs underneath.
  - flag   : held for human review; nothing is submitted.
  - refuse : blocked; nothing is submitted.
  - a tampered passport (HMAC fails) or a design that does not match the passport (inputs_hash mismatch) is REJECTED;
    nothing is submitted - even if pen-stack's own gate would have allowed it.
The gate decision + the design hash are written to the hash-chained audit log (tamper-evident).

This is the MECHANISM, not a deployed execution authority; pen-stack's cloud-lab endpoint is mock/dry-run today, so
the tests assert the interception contract, not a real wet run.
"""
from __future__ import annotations

import hashlib
import json

from bio_firewall.adapters.generic_artifact import normalize
from bio_firewall.passport.sign import verify_passport


def _inputs_hash(design: dict) -> str:
    """The passport's inputs_hash basis: sha256 over the canonical normalized plan (mirrors passport/sign.py)."""
    plan = normalize(design)
    return hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def passport_matches_design(passport: dict, design: dict) -> bool:
    """True iff the passport is HMAC-intact AND its inputs_hash matches THIS design (defeats passport reuse on a
    mutated/substituted design)."""
    return bool(passport) and verify_passport(passport) and passport.get("inputs_hash") == _inputs_hash(design)


def _default_submit_fn(design: dict, experiment: dict, **kw):
    """Lazy, guarded call into pen-stack's cloud-lab submit (mirrors the cargo axis's guarded coupling)."""
    from pen_stack.build.cloudlab import submit_gated   # noqa: PLC0415 - lazy: optional heavy dependency surface
    return submit_gated(design, experiment, **kw)


def gated_cloudlab_submit(design: dict, experiment: dict | None = None, *, passport: dict | None = None,
                          submit_fn=None, audit=None, **submit_kw) -> dict:
    """Gate a cloud-lab submission on a verified BioFirewall `allow` passport.

    If `passport` is None, the design is screened fresh (the normal in-workflow path) and the minted passport is used.
    If a `passport` is supplied (carried from an earlier `screen()`), it is verified against THIS design and only an
    intact, matching, `allow` passport proceeds. `submit_fn(design, experiment, **kw)` defaults to pen-stack's
    `submit_gated`; inject a stub in tests. Returns a structured result; never raises on a block.
    """
    from bio_firewall.intercept.spine import screen     # lazy: avoid the adapters<->spine import cycle
    experiment = experiment or {}
    submit_fn = submit_fn or _default_submit_fn

    if passport is None:                                  # fresh in-workflow screen
        verdict = screen(design)
        passport = verdict["passport"]
        decision = verdict["decision"]
    else:                                                 # carried passport: trust ONLY if intact + matches the design
        if not passport_matches_design(passport, design):
            result = {"submitted": False, "blocked": True, "decision": "rejected",
                      "reason": "passport invalid or does not match this design (tamper-evident gate)",
                      "gate": "bio-firewall stage-K"}
            _audit(audit, design, result)
            return result
        decision = passport.get("decision", "refuse")

    if decision != "allow":
        result = {"submitted": False, "blocked": decision == "refuse", "held": decision == "flag_for_review",
                  "decision": decision, "passport": passport, "gate": "bio-firewall stage-K",
                  "reason": ("hard hazard - blocked" if decision == "refuse" else "flagged - held for human review")}
        _audit(audit, design, result)
        return result

    # allow: carry the passport with the submission and call through to pen-stack (its own gate runs underneath)
    experiment = {**experiment, "biofirewall_passport": passport}
    penstack_result = submit_fn(design, experiment, **submit_kw)
    result = {"submitted": True, "blocked": False, "decision": "allow", "passport": passport,
              "gate": "bio-firewall stage-K", "penstack_result": penstack_result}
    _audit(audit, design, result)
    return result


def _audit(audit, design: dict, result: dict) -> None:
    if audit is not None:
        audit.append({"event": "cloudlab_gate", "design_hash": _inputs_hash(design),
                      "decision": result["decision"], "submitted": result["submitted"]})
