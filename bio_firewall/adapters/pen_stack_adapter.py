"""Reference integration: govern a PEN-STACK design plan. PEN-STACK is the design tool; BioFirewall supervises it.
Maps a PEN-STACK design dict onto the generic artifact and screens it; the cross-check against PEN-STACK's own
in-design verdict is realized in `reconcile.py`. NOTE: pen-stack has no top-level `verify()`/`Verdict`; the
in-design verdict is `pen_stack.safety.safety_gate(design) -> SafetyVerdict`, which `reconcile()` consumes."""
from __future__ import annotations


def govern_pen_stack_design(design: dict, *, reconcile_penstack: bool = False) -> dict:
    """Screen a PEN-STACK design (gene/chrom/edit_intent/delivery_vehicle/cargo_function) via the five-axis firewall.
    With `reconcile_penstack=True`, also take the conservative meet with pen-stack's own in-design SafetyVerdict
    (`reconcile.py`) and attach it under `verdict['reconcile']`."""
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
    verdict = screen(artifact)
    if reconcile_penstack:
        from bio_firewall.adapters.reconcile import reconcile
        verdict["reconcile"] = reconcile(artifact)
    return verdict
