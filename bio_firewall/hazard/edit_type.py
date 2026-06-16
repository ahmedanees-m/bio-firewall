"""Axis 3 — EDIT-TYPE (the operation). Oncogenic-fusion-by-design (hard_reject, against a curated open fusion set),
multiplex translocation, large deletion. A declared fusion of two genes NOT on the known-oncogenic list is still
flagged (unknown oncogenicity is a known-unknown)."""
from __future__ import annotations

from bio_firewall.data import is_oncogenic_fusion
from bio_firewall.hazard.finding import Finding, finding


def screen_edit(plan: dict) -> Finding:
    e = plan.get("edit") or {}
    fg = e.get("fusion_genes") or e.get("fusion_partners")
    if fg and len(fg) == 2:
        rec = is_oncogenic_fusion(fg[0], fg[1])
        if rec:
            return finding("hard_reject", "edit.oncogenic_fusion_by_design", "edit_type",
                           f"breakpoint creates the known oncogenic fusion {rec.get('name')} ({rec.get('cancer')}) by design",
                           provenance={"source": "curated open oncogenic-fusion set", "citation": [rec.get("citation")]})
        return finding("soft_penalty", "edit.fusion_unknown_oncogenicity", "edit_type",
                       f"designed gene fusion {fg[0]}-{fg[1]} of unknown oncogenicity — flag for review", extrapolating=True)
    if e.get("fusion") or e.get("oncogenic_fusion"):
        return finding("hard_reject", "edit.oncogenic_fusion_by_design", "edit_type",
                       "breakpoint creates an oncogenic fusion by design")
    dsb = int(e.get("concurrent_dsb", 0) or 0)
    if dsb >= 3:
        return finding("soft_penalty", "edit.multiplex_translocation", "edit_type",
                       f"{dsb} concurrent multi-locus DSBs raise translocation risk")
    deleted = int(e.get("deleted_bp", 0) or 0)
    if deleted >= 50_000:
        return finding("soft_penalty", "edit.large_deletion", "edit_type",
                       f"large deletion ({deleted} bp) — check essential/TSG content", extrapolating=True)
    return finding("clear", None, "edit_type", "no edit-type hazard signal")
