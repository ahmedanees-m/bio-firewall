"""The tool-agnostic artifact contract — maps any design AI's output onto the five-axis plan. This is what makes
"supervises any design AI" true: Biomni / CRISPR-GPT / a raw design all normalize to the same plan shape."""
from __future__ import annotations


def normalize(artifact: dict) -> dict:
    """Permissively map an artifact onto the five-axis plan contract. Missing axes default to empty (-> clear)."""
    if not isinstance(artifact, dict):
        raise TypeError("artifact must be a dict")
    return {
        "intent": artifact.get("intent") or artifact.get("purpose") or "",
        "cargo": artifact.get("cargo") or {"function": artifact.get("cargo_function")},
        "locus": artifact.get("locus") or {"gene": artifact.get("gene"), "chrom": artifact.get("chrom"),
                                           "cell_type": artifact.get("cell_type")},
        "edit": artifact.get("edit") or {},
        "germline": artifact.get("germline") or {},
        "scale": artifact.get("scale") or {},
        "delivery_vehicle": artifact.get("delivery_vehicle"),
    }
