"""The tool-agnostic artifact contract - maps any design AI's output onto the five-axis plan. This is what makes
"supervises any design AI" true: Biomni / CRISPR-GPT / a raw design all normalize to the same plan shape."""
from __future__ import annotations


# Keys the contract maps. Anything else is dropped before screening, which is what makes the
# contract tool-agnostic and is also how a hazard-bearing field submitted under an unexpected name
# escapes every rule. `unmapped_keys` makes that visible rather than silent.
_MAPPED = frozenset({
    "intent", "purpose", "cargo", "cargo_function", "locus", "gene", "chrom", "pos", "cell_type",
    "edit", "germline", "scale", "delivery_vehicle",
})


def unmapped_keys(artifact: dict) -> list[str]:
    """Top-level keys the five-axis contract does not read, and so does not screen."""
    if not isinstance(artifact, dict):
        return []
    return sorted(k for k in artifact if k not in _MAPPED)


def normalize(artifact: dict) -> dict:
    """Permissively map an artifact onto the five-axis plan contract. Missing axes default to empty (-> clear)."""
    if not isinstance(artifact, dict):
        raise TypeError("artifact must be a dict")
    return {
        "intent": artifact.get("intent") or artifact.get("purpose") or "",
        "cargo": artifact.get("cargo") or {"function": artifact.get("cargo_function")},
        "locus": artifact.get("locus") or {"gene": artifact.get("gene"), "chrom": artifact.get("chrom"),
                                           "pos": artifact.get("pos"), "cell_type": artifact.get("cell_type")},
        "edit": artifact.get("edit") or {},
        "germline": artifact.get("germline") or {},
        "scale": artifact.get("scale") or {},
        "delivery_vehicle": artifact.get("delivery_vehicle"),
    }
