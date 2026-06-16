"""Axis 4 — GERMLINE / HERITABLE  [genuinely NEW — no PEN-STACK coverage].

Flags the heritability / germline-accessibility of a write plan. A regulatory/policy axis: it FLAGS and routes
to human / IRB / ESCRO review — it does NOT adjudicate ethics. `hard_reject` only for the unambiguous (human
heritable CLINICAL editing — the He Jiankui line, prohibited); embryo/germ-cell research is `scope_flag` to
declared oversight; non-therapeutic enhancement on a heritable target is a `soft_penalty`.
"""
from __future__ import annotations

from bio_firewall.hazard.finding import Finding, finding

# germline-accessible (heritable) target cell types vs somatic
_GERMLINE_CELLS = {"zygote", "embryo", "oocyte", "egg", "sperm", "spermatocyte", "spermatogonia",
                   "germ_cell", "germline", "blastocyst", "pgc", "primordial_germ_cell", "gamete"}
_PLURIPOTENT = {"ipsc", "esc", "embryonic_stem_cell", "pluripotent", "hesc"}   # germline-competent in some contexts
_ENHANCEMENT = ("enhance", "enhancement", "augment", "iq", "intelligence", "muscle mass", "height",
                "cosmetic", "eye colour", "eye color", "non-therapeutic", "designer")


def _norm(s: object) -> str:
    return str(s or "").strip().lower().replace("-", "_").replace(" ", "_")


def _is_enhancement(plan: dict) -> bool:
    text = " ".join(str(plan.get(k, "")) for k in ("intent", "purpose")).lower()
    return any(t in text for t in _ENHANCEMENT)


def screen_germline(plan: dict) -> Finding:
    g = plan.get("germline") or {}
    ct = _norm(g.get("cell_type") or (plan.get("locus") or {}).get("cell_type"))
    organism = _norm(g.get("organism") or "human")
    is_human = organism in ("human", "homo_sapiens", "")
    heritable = bool(g.get("heritable")) or ct in _GERMLINE_CELLS
    clinical = bool(g.get("clinical"))

    if is_human and heritable and clinical:
        return finding("hard_reject", "germline.human_heritable_clinical", "germline",
                       "human germline / heritable CLINICAL edit (prohibited under the WHO framework + national law)",
                       provenance={"source": "WHO human-genome-editing framework; national prohibitions"})
    if is_human and (ct in _GERMLINE_CELLS or ct in _PLURIPOTENT):
        return finding("scope_flag", "germline.human_embryo_research", "germline",
                       "human embryo / germ-cell / pluripotent target — route to declared IRB/ESCRO oversight",
                       provenance={"note": "research is permitted under oversight in many jurisdictions; not adjudicated here"})
    if heritable and _is_enhancement(plan):
        return finding("soft_penalty", "germline.enhancement_nontherapeutic", "germline",
                       "heritable target with a non-therapeutic enhancement intent")
    return finding("clear", None, "germline", "somatic / non-heritable target — no germline-accessibility signal")
