"""The per-axis Finding contract + decision ordering (shared by all five axes)."""
from __future__ import annotations

from dataclasses import dataclass, field

# decision severity ordering (worst first). hard_reject blocks; soft_penalty/scope_flag -> flag-for-review.
SEVERITY = {"hard_reject": 3, "scope_flag": 2, "soft_penalty": 1, "clear": 0}


@dataclass
class Finding:
    decision: str                 # hard_reject | scope_flag | soft_penalty | clear
    rule_id: str | None
    axis: str                     # cargo | locus | edit_type | germline | scale
    mechanism: str                # plain-language WHY (the evidence text)
    provenance: dict = field(default_factory=dict)
    score: float | None = None    # optional 0-1 axis score
    extrapolating: bool = False    # honesty: mechanism-grounded flag, not a validated prediction

    def as_dict(self) -> dict:
        return {"decision": self.decision, "rule_id": self.rule_id, "axis": self.axis,
                "mechanism": self.mechanism, "provenance": self.provenance, "score": self.score,
                "extrapolating": self.extrapolating}


def finding(decision: str, rule_id: str | None, axis: str, mechanism: str, *,
            provenance: dict | None = None, score: float | None = None, extrapolating: bool = False) -> Finding:
    return Finding(decision, rule_id, axis, mechanism, provenance or {}, score, extrapolating)
