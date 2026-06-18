"""Response shaping (v0.8.0, WS-GRADED): the graded-refusal taxonomy that formalizes the stratified verdict into
allow / partial / flag_for_review / refuse, plus a deterministic content gate that verifies a `partial` response
carries general context only (no actionable/operational detail)."""
from bio_firewall.respond.graded import (  # noqa: F401
    GRADES,
    content_gate,
    grade,
    graded_response,
    partial_response,
)

__all__ = ["GRADES", "content_gate", "grade", "graded_response", "partial_response"]
