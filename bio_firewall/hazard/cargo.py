"""Axis 1 — CARGO (what you insert). REUSES PEN-STACK's Guardian (Pfam/InterPro + Select-Agent + Australia-Group,
framing-stripped, no hazard sequences), PLUS a function-aware ESM2 layer (cargo_ml) that catches low-identity
toxin homologs which evade signature/homology screens. The Guardian's declared-function REFUSE wins; the
probabilistic function-aware signal routes to REVIEW (scope_flag)."""
from __future__ import annotations

from functools import lru_cache

from bio_firewall.hazard.cargo_ml import function_aware_score
from bio_firewall.hazard.finding import Finding, finding


@lru_cache(maxsize=4096)
def _guardian(func: str) -> tuple[str, str] | None:
    """(decision, reason) from the PEN-STACK Guardian for a cargo function, or None if unavailable. Cached:
    identical cargo functions (the common case — a fixed cassette across many loci) screen once."""
    try:
        from pen_stack.safety import safety_gate
        v = safety_gate({"cargo_function": func}, actor="biofirewall")
        return (getattr(v, "decision", "clear"), getattr(v, "reason", None) or "Guardian signature screen")
    except Exception:  # noqa: BLE001 - Guardian unavailable -> fall through (never crash)
        return None


def screen_cargo(plan: dict) -> Finding:
    cargo = plan.get("cargo") or {}
    func = str(cargo.get("function") or plan.get("intent") or "")
    seq = cargo.get("sequence")
    got = _guardian(func)
    if got is not None:
        d, reason = got
        prov = {"source": "PEN-STACK Guardian (Pfam/InterPro + Select-Agent 42CFR73/7CFR331/9CFR121 + Australia-Group)"}
        if d == "refuse":
            return finding("hard_reject", "cargo.select_agent_or_toxin", "cargo", reason, provenance=prov)
        if d == "escalate":
            return finding("scope_flag", "cargo.dual_use_escalate", "cargo",
                           reason + " — ambiguous dual-use (e.g. gain-of-function) routed to oversight (P3CO/DURC)", provenance=prov)
        if d == "flag":
            return finding("soft_penalty", "cargo.flag", "cargo", reason, provenance=prov)
    if any(t in func.lower() for t in ("gene drive", "gene_drive", "homing endonuclease drive")):
        return finding("hard_reject", "cargo.gene_drive", "cargo",
                       "self-propagating gene-drive cassette in a releasable context")
    # function-aware ML: a cargo SEQUENCE whose ESM2 embedding leans toxin (low-identity homolog) -> route to review.
    score, available = function_aware_score(seq)
    if available and score is not None and score > 0.02:
        return finding("scope_flag", "cargo.function_aware_ml", "cargo",
                       f"function-aware ESM2 screen flags a toxin-leaning cargo (lean-score {score:+.3f}) that may evade "
                       "signature/homology screens — route to review",
                       provenance={"source": "ESM2 nearest-centroid (public toxin/benign refs)"}, score=score, extrapolating=True)
    return finding("clear", None, "cargo", "no cargo hazard signature")
