"""Axis 5 — SCALE (the magnitude). A magnitude/uncertainty AMPLIFIER: large scale widens intervals and lowers
the abstention threshold rather than asserting a specific harm. Phase-1 applies Axes 2-3 across all affected regions."""
from __future__ import annotations

from bio_firewall.hazard.finding import Finding, finding

_MB = 1_000_000


def screen_scale(plan: dict) -> Finding:
    s = plan.get("scale") or {}
    total_bp = int(s.get("total_bp", 0) or 0)
    n_edits = int(s.get("n_edits", 1) or 1)
    if total_bp >= _MB:
        return finding("soft_penalty", "scale.megabase_restructuring", "scale",
                       f"total affected span {total_bp:,} bp exceeds 1 Mb — aggregate effect unmodelable; widen intervals",
                       extrapolating=True)
    if n_edits >= 10:
        return finding("scope_flag", "scale.high_multiplex", "scale",
                       f"{n_edits} concurrent edits — high multiplex; lower the abstention threshold")
    return finding("clear", None, "scale", "scale within modelable bounds")
