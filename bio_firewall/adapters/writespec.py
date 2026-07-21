"""Screen the typed PEN-STACK WriteRequest (SBOL3 profile) directly.

BioFirewall normally screens a `design: dict`. `pen_stack.spec.WriteRequest` is a typed, ontology-backed intent
object with resolved HGNC genes, GRCh38 coordinates, and Sequence-Ontology cargo roles. Screening it directly is
strictly more precise (the locus axis gets resolved coordinates; the cargo axis gets SO roles) and removes a parsing
step. The mapping is duck-typed: it works with a real `WriteRequest` (pydantic) or any object/dict of the same shape,
so it does not import or depend on pen-stack at module load. The dict path remains the default; this is additive.

Fail-closed contract: where a hazard-relevant field is null/unresolved, BioFirewall screens what IS present and
raises a SCOPE FLAG for the unresolved field rather than assuming safety - it never silently allows on missing
where/what.
"""
from __future__ import annotations

import re

_INSERTION_LIKE = {"insertion", "replacement", "landing_pad_install", "regulatory_rewrite"}
_CARGO_BEARING = {"insertion", "replacement", "landing_pad_install"}
_COORD = re.compile(r"chr?([0-9XYMT]+)\s*[:_-]\s*(\d+)", re.I)


def _g(obj, attr, default=None):
    """Read `attr` from a pydantic/object (getattr) or a dict (get) - duck-typed."""
    if obj is None:
        return default
    return obj.get(attr, default) if isinstance(obj, dict) else getattr(obj, attr, default)


def _resolved_value(r):
    """The usable string of a Resolved field: prefer the ontology label, then the free text (None if absent)."""
    if r is None:
        return None
    if isinstance(r, str):
        return r
    return _g(r, "label") or _g(r, "text")


def _cargo_desc(c):
    name = _g(c, "name")
    role = _resolved_value(_g(c, "role"))
    return " ".join(p for p in (name, role) if p) or None


def writerequest_to_plan(wr) -> tuple[dict, list[str]]:
    """Map a WriteRequest(-shaped) object to a firewall plan, and list the hazard-relevant fields left unresolved."""
    target = _g(wr, "target")
    cargo_list = _g(wr, "cargo") or []
    wtype = _g(wr, "write_type")
    free = _g(wr, "free_text_note")

    gene = _resolved_value(_g(target, "gene"))
    locus_text = _resolved_value(_g(target, "locus"))
    m = _COORD.search(locus_text) if locus_text else None
    chrom, pos = (m.group(1), int(m.group(2))) if m else (None, None)
    cargo_desc = "; ".join(d for d in (_cargo_desc(c) for c in cargo_list) if d) or None

    plan = {
        "intent": free or cargo_desc or (wtype or ""),
        "cargo_function": cargo_desc,
        "gene": gene,
        "chrom": chrom,
        "pos": pos,
        "cell_type": _resolved_value(_g(wr, "cell_type")),
        "edit": {"write_type": wtype} if wtype else {},
    }
    unresolved: list[str] = []
    if wtype in _INSERTION_LIKE and not (gene or chrom):
        unresolved.append("locus")                  # an insertion with no resolved where -> cannot screen the locus axis
    if wtype in _CARGO_BEARING and not cargo_desc:
        unresolved.append("cargo")                  # a cargo-bearing write with no cargo descriptor -> cannot screen what
    return plan, unresolved


def screen_writerequest(wr, *, audit=None) -> dict:
    """Screen a typed WriteRequest. Returns the firewall verdict with an added `writespec` block; a hazard-relevant
    unresolved field escalates a clean `allow` to `flag_for_review` (a scope flag), never a silent allow."""
    from bio_firewall.intercept.spine import screen   # lazy: avoid the adapters<->spine import cycle
    plan, unresolved = writerequest_to_plan(wr)
    v = dict(screen(plan))
    v["writespec"] = {"unresolved_hazard_fields": unresolved, "plan": plan}
    if unresolved and v["decision"] == "allow":
        v["decision"] = "flag_for_review"
        v["writespec"]["scope_flag"] = ("unresolved hazard-relevant field(s): " + ", ".join(unresolved)
                                        + "; screened what is present, not asserting safety")
    if audit is not None:
        audit.append({"event": "writespec_screen", "decision": v["decision"], "unresolved": unresolved})
    return v
