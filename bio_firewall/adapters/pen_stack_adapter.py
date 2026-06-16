"""Reference integration: govern a PEN-STACK design plan. PEN-STACK is the design tool; BioFirewall supervises it.
Maps a PEN-STACK design dict onto the generic artifact, screens it, and (Phase-1) cross-checks via PEN-STACK's
verify()/Verdict over the MCP/REST surface."""
from __future__ import annotations


def govern_pen_stack_design(design: dict) -> dict:
    """Screen a PEN-STACK design (gene/chrom/edit_intent/delivery_vehicle/cargo_function) via the five-axis firewall.
    Phase-1 will also call pen_stack.verify() and reconcile legality + the firewall verdict."""
    artifact = {
        "intent": design.get("cargo_function") or design.get("edit_intent") or "",
        "cargo_function": design.get("cargo_function"),
        "gene": design.get("gene"),
        "chrom": design.get("chrom"),
        "cell_type": design.get("cell_type"),
        "delivery_vehicle": design.get("delivery_vehicle"),
        "edit": {"concurrent_dsb": len(design.get("edits", [])) or None} if design.get("edits") else {},
    }
    from bio_firewall.intercept.spine import screen          # lazy import: avoid the adapters<->spine cycle
    return screen(artifact)
