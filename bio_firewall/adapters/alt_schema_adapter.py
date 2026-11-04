"""Second reference adapter: a planner whose plan schema uses different field names.

The field vocabulary here (`task`, `target_gene`, `cell_line`, `payload_function`) is defined for this
adapter rather than taken from any released planner's interface, and no third-party tool is called. The
adapter renames those fields onto the shared five-axis artifact and calls the same `screen` the PEN-STACK
adapter calls, so a substantively identical plan reaches the same decision through either adapter.
Interoperability with an independently developed planner is not demonstrated.
"""
from __future__ import annotations


def govern_alt_schema_plan(plan: dict, *, reconcile_penstack: bool = False) -> dict:
    """Screen a plan given in this adapter's field vocabulary through the five-axis firewall.

    Thin by design: it renames the planner's fields onto the artifact and calls the same `screen` the
    PEN-STACK adapter calls.
    """
    edit: dict = {}
    if plan.get("fusion_genes"):
        edit["fusion_genes"] = plan["fusion_genes"]
    if plan.get("n_edits") and int(plan["n_edits"]) > 1:
        edit["concurrent_dsb"] = int(plan["n_edits"])
    artifact = {
        "intent": plan.get("task") or plan.get("goal") or plan.get("objective") or "",
        "cargo": {"function": plan.get("payload_function") or plan.get("payload")},
        "gene": plan.get("target_gene") or plan.get("gene"),
        "chrom": plan.get("chromosome") or plan.get("chrom"),
        "cell_type": plan.get("cell_line") or plan.get("cell_type"),
        "delivery_vehicle": plan.get("vector") or plan.get("delivery"),
        "germline": plan.get("germline"),
        "scale": {"total_bp": int(plan["insert_bp"])} if plan.get("insert_bp") else {},
        "edit": edit,
    }
    from bio_firewall.intercept.spine import screen  # lazy import: avoid the adapters<->spine cycle
    verdict = screen(artifact)
    if reconcile_penstack:
        from bio_firewall.adapters.reconcile import reconcile
        verdict["reconcile"] = reconcile(artifact)
    return verdict
