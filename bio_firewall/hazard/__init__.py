"""The five-axis write-plan hazard screen (P2 — the differentiator)."""
from __future__ import annotations

from bio_firewall.hazard.cargo import screen_cargo
from bio_firewall.hazard.combine import combine
from bio_firewall.hazard.edit_type import screen_edit
from bio_firewall.hazard.germline import screen_germline
from bio_firewall.hazard.locus import screen_locus
from bio_firewall.hazard.scale import screen_scale


def five_axis_screen(plan: dict) -> dict:
    """Run all five genome-writing-native axes and stratify into one verdict (allow / flag_for_review / refuse)."""
    findings = [screen_cargo(plan), screen_locus(plan), screen_edit(plan),
                screen_germline(plan), screen_scale(plan)]
    return combine(findings)


__all__ = ["five_axis_screen", "screen_cargo", "screen_locus", "screen_edit", "screen_germline", "screen_scale"]
