"""Second reference integration: govern a CRISPR-GPT-shaped design plan. This exists to demonstrate, not merely
assert, that the artifact contract is not PEN-STACK-specific. The plan schema here is a mock of the CRISPR-GPT /
Biomni family - it uses different field names than PEN-STACK's design dict (`task`/`target_gene`/`cell_line`/
`payload_function` rather than `edit_intent`/`gene`/`cell_type`/`cargo_function`) - and this thin adapter maps them
onto the shared five-axis artifact and screens it. A plan of the same substance receives the same decision whichever
tool produced it, which is the point: the governance layer does not depend on the tool it sits in front of.
"""
from __future__ import annotations


def govern_crispr_gpt_plan(plan: dict, *, reconcile_penstack: bool = False) -> dict:
    """Screen a CRISPR-GPT-shaped plan via the five-axis firewall. The adapter is deliberately thin: it renames the
    planner's fields onto the artifact and calls the same `screen` the PEN-STACK adapter calls."""
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
