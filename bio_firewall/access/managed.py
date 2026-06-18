"""P9 managed-access plane: assign an ACCESS TIER from (verdict severity, verified user-legitimacy level) and gate
the RESOLUTION of the verdict accordingly. Bind the tier + legitimacy evidence into the signed passport (P4) and the
hash-chained audit (P7) so the resolution is tamper-evident.

Grounding: NTI, "A Framework for Managed Access to Biological AI Tools" (NTI|bio, 2026-01-28) - tiered access by
risk level + user legitimacy as "a foundation for other built-in guardrails, reducing the risk that such guardrails
will be avoided or removed"; ABC-Bench (NeurIPS 2025 Workshop BioSafe GenAI, arXiv:2606.11150) - tiered/KYC access
for accredited researchers. The contribution is the BUILT MECHANISM that implements NTI's second guardrail,
tool-agnostically; the credentialing authority is an integration point, not an operational claim here.

Determinism: `resolve(decision, legitimacy_rank, low_confidence)` is a total function over a small finite domain, so
the same (verdict, tier) always yields the same resolution - the pre-registered (verdict x tier) matrix.
"""
from __future__ import annotations

import hashlib
import json

from bio_firewall.passport.sign import sign_passport

# Ordered user-legitimacy levels (NTI: legitimacy verified by the deployment's credentialing authority via a hook).
#   unverified  : no credential supplied
#   declared    : self-declared affiliation + purpose, NOT verified
#   verified    : institutional affiliation verified through the deployment's verification hook
#   credentialed: verified + prior-attestation / accredited-researcher KYC (the highest legitimacy)
LEGITIMACY = {"unverified": 0, "declared": 1, "verified": 2, "credentialed": 3}
_VERIFIED = LEGITIMACY["verified"]

# The resolution a managed verdict can take. A refuse is NEVER unlocked by access tier (a hard hazard stays refused);
# managed access gates how a clear/flag verdict is RELEASED, and escalates a low-confidence (out-of-KB) allow.
RESOLUTIONS = ("released", "released_with_review", "held_pending", "refused")


def _canonical(body: dict) -> bytes:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode()


def required_legitimacy(decision: str, low_confidence: bool) -> int:
    """The minimum legitimacy rank for an UNCONDITIONAL release. refuse -> unreachable (4: never releases); a
    flag, or a low-confidence (out-of-KB) allow, requires a VERIFIED user to proceed (else held); a confident allow
    requires nothing."""
    if decision == "refuse":
        return 4                                  # above the max legitimacy rank: a refuse never releases
    if decision == "flag_for_review" or low_confidence:
        return _VERIFIED
    return 0


def resolve(decision: str, legitimacy_rank: int, *, low_confidence: bool = False) -> str:
    """Deterministic, total (verdict x tier) resolution.
      refuse                          -> refused                (hard hazard; access tier never unlocks it)
      flag_for_review, verified+      -> released_with_review   (proceeds under human review / monitoring)
      flag_for_review, unverified     -> held_pending           (cannot proceed until legitimacy verified + reviewed)
      allow + out-of-KB, verified+    -> released_with_review   (the competence boundary escalates one notch)
      allow + out-of-KB, unverified   -> held_pending
      allow (confident, in-KB)        -> released               (clean clear, any tier)."""
    if decision == "refuse":
        return "refused"
    if decision == "flag_for_review":
        return "released_with_review" if legitimacy_rank >= _VERIFIED else "held_pending"
    # decision == "allow"
    if low_confidence:                            # out-of-KB locus (P8 competence boundary) -> escalate a tier
        return "released_with_review" if legitimacy_rank >= _VERIFIED else "held_pending"
    return "released"


def apply_access(verdict: dict, plan: dict, *, legitimacy: str = "unverified", evidence: dict | None = None,
                 verification_hook: str = "none", audit=None) -> dict:
    """Resolve a screened verdict under a user-legitimacy level, bind the tier + legitimacy evidence into a re-signed
    passport (tamper-evident) and, optionally, the hash-chained audit. Returns the access record (with its passport).

    `evidence` carries the auditable legitimacy claim (institutional affiliation, declared purpose, prior-attestation);
    `verification_hook` names the pluggable credentialing check the deployment ran (the authority is its integration
    point, not this plane). Does NOT mutate `verdict`."""
    if legitimacy not in LEGITIMACY:
        raise ValueError(f"unknown legitimacy level {legitimacy!r}; expected one of {sorted(LEGITIMACY)}")
    rank = LEGITIMACY[legitimacy]
    decision = verdict["decision"]
    low_conf = verdict.get("calibrated_confidence") == "low"      # out-of-KB competence boundary (P8)
    resolution = resolve(decision, rank, low_confidence=low_conf)
    evidence = evidence or {}
    record = {
        "schema": "biofirewall/access@1",
        "decision": decision,
        "legitimacy_level": legitimacy,
        "legitimacy_rank": rank,
        "low_confidence_locus": low_conf,
        "required_legitimacy_rank": required_legitimacy(decision, low_conf),
        "resolution": resolution,
        "evidence_hash": hashlib.sha256(_canonical(evidence)).hexdigest(),
        "verification_hook": verification_hook,
        "credentialing_authority": "integration_point",          # documented, NOT claimed operational
    }
    # bind the access tier into a re-signed passport: mutating the tier/resolution breaks this signature.
    record["passport"] = sign_passport(plan, verdict, access=record)
    if audit is not None:
        audit.append({"event": "access_resolution", "inputs_hash": record["passport"]["inputs_hash"],
                      "decision": decision, "legitimacy_level": legitimacy,
                      "evidence_hash": record["evidence_hash"], "resolution": resolution})
    return record


def verify_access(access: dict) -> bool:
    """True iff the access record's bound passport signature is intact under the current deployment key (tamper-
    evident): any change to the legitimacy level, resolution, or required tier invalidates it."""
    from bio_firewall.passport.sign import verify_passport
    return verify_passport(access.get("passport", {}))


def screen_managed(artifact: dict, *, legitimacy: str = "unverified", evidence: dict | None = None,
                   verification_hook: str = "none", audit=None) -> dict:
    """One-call managed entry point: run the five-axis screen (P1-P8), then resolve under the access tier (P9). The
    returned verdict carries an `access` block (tier + resolution + bound passport). The base verdict is unchanged, so
    every existing guarantee (decision, evidence, calibrated confidence) still holds."""
    from bio_firewall.adapters.generic_artifact import normalize
    from bio_firewall.intercept.spine import screen
    plan = normalize(artifact)
    verdict = screen(artifact, audit=audit)
    verdict["access"] = apply_access(verdict, plan, legitimacy=legitimacy, evidence=evidence,
                                     verification_hook=verification_hook, audit=audit)
    return verdict
