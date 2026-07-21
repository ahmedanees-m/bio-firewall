"""Axis 1 - CARGO (what you insert). REUSES PEN-STACK's Guardian (Pfam/InterPro + Select-Agent + Australia-Group,
framing-stripped, no hazard sequences), PLUS a function-aware ESM2 layer (cargo_ml) that catches low-identity
toxin homologs which evade signature/homology screens. The Guardian's declared-function REFUSE wins; the
probabilistic function-aware signal routes to REVIEW (scope_flag)."""
from __future__ import annotations

import unicodedata
from functools import lru_cache

from bio_firewall.hazard.cargo_ml import function_aware_score
from bio_firewall.hazard.finding import Finding, finding


# --- BioFirewall-native select-agent signatures (defense in depth) -------------------------------------------------
# The Guardian is the primary cargo screen, but it is an UPSTREAM dependency: it is unreachable from a wheel install
# of pen-stack, and it matches listed names as whole words, so an indirect naming ("Ricinus communis agglutinin
# toxin" for ricin) reads as clear. A biosecurity screen must not be blind to a listed toxin because the design tool
# it supervises is absent or because the hazard was addressed by another name, so the cargo axis carries its own
# name-level signatures. Names and taxa only; no hazard sequences.
_LIST_PROV = ("BioFirewall hazard KB: select-agent and Australia-Group listed toxins and their source organisms "
              "(42 CFR 73, 7 CFR 331, 9 CFR 121; Australia Group control list). Names and taxa only, no sequences.")

# Listed select-agent / Australia-Group toxins. Includes canonical abbreviations (SEB) and gene names (stx1, stx2)
# because those are the standard names in GenBank / UniProt / primary literature, and a name-only screen that misses
# the canonical name is a bypass.
SELECT_AGENT_TOXINS = frozenset({
    "ricin", "abrin", "botulinum neurotoxin", "botulinum toxin", "shiga toxin", "shiga-like toxin",
    "staphylococcal enterotoxin", "diphtheria toxin", "epsilon toxin", "conotoxin", "saxitoxin",
    "tetrodotoxin", "t-2 toxin", "t2 toxin", "anthrax lethal toxin",
    # canonical abbreviations for the staphylococcal enterotoxins (SEA-SEE) - the standard forms in the
    # primary literature and in GenBank protein records
    "seb", "sea", "sec", "sed", "see",
    # canonical gene/protein names for shiga toxin variants (EHEC clinical + UniProt/GenBank standard)
    "stx1", "stx2", "stxa", "stxb",
})

# Source organisms of listed toxins. Naming an organism ALONE is ordinary microbiology and is NOT screened; it is
# screened only together with a toxin descriptor, which is how a listed toxin is named indirectly. Genus-only
# shorthand ('ricinus', 'abrus') is included for the monotypic-genus cases where the genus name is standard
# scientific shorthand for the species. Clostridium is kept as a binomial (many benign species; C. difficile).
SELECT_AGENT_TOXIN_ORGANISMS = frozenset({
    "ricinus communis", "ricinus",
    "abrus precatorius", "abrus",
    "clostridium botulinum",
    "clostridium perfringens",
    "shigella dysenteriae",
    "staphylococcus aureus",
    "corynebacterium diphtheriae",
    "bacillus anthracis",
})

# Definitive toxin descriptors: paired with a listed source organism, refuse. 'epsilon' is included because that
# is the CFR-listing name of Clostridium perfringens epsilon toxin.
_TOXIN_DESCRIPTORS_STRONG = ("toxin", "neurotoxin", "enterotoxin", "ribosome-inactivating",
                             "rip type-2", "rip type 2", "epsilon")

# Ambiguous descriptors: agglutinin and lectin are the standard names for ricin AND for the distinct non-select
# lectins (e.g. RCA-I / RCA120) that share Ricinus communis as a source. Paired with a listed organism, refuse -
# except when an explicit distinct-lectin identifier ('rca-i', 'rca120', 'mannose-binding lectin') is present,
# in which case route to review (flag_for_review) rather than hard-reject.
_TOXIN_DESCRIPTORS_AMBIGUOUS = ("agglutinin", "lectin")

# All descriptors used by the indirect check (union of strong + ambiguous).
_TOXIN_DESCRIPTORS = _TOXIN_DESCRIPTORS_STRONG + _TOXIN_DESCRIPTORS_AMBIGUOUS

# Distinct non-select lectin identifiers. RCA-I / RCA120 is the Ricinus communis agglutinin used as a research
# reagent (mannose-binding lectin); a plan that names it explicitly downgrades a Ricinus+lectin/agglutinin
# indirect hit from refuse to flag_for_review (still routed to human oversight).
_NON_SELECT_LECTIN_MARKERS = ("rca-i", "rca120", "rca 120", "mannose-binding lectin", "mannose binding lectin")

# Negators: an occurrence of a toxin descriptor immediately preceded by one of these is NOT read as an
# affirmative descriptor (e.g. 'no toxin work' is a scope disclaimer, not an indirect toxin naming).
_NEGATORS = frozenset({"no", "not", "without", "excluding", "absent", "sans", "avoiding", "lacking"})

_WORD_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-")

# Common Cyrillic / Greek code points that visually resemble Latin letters (confusables fold). NFKC handles
# fullwidth ASCII and canonical compatibility characters; this table covers homoglyphs that NFKC leaves as
# their own script's letter. A single homoglyph must not flip a select-agent name from refuse to allow.
_CONFUSABLES = str.maketrans({
    # Cyrillic look-alikes
    "а": "a", "А": "a",   # а А
    "е": "e", "Е": "e",   # е Е
    "о": "o", "О": "o",   # о О
    "р": "p", "Р": "p",   # р Р
    "с": "c", "С": "c",   # с С
    "х": "x", "Х": "x",   # х Х
    "у": "y", "У": "y",   # у У
    "і": "i", "І": "i",   # і І (Ukrainian / Belarusian)
    "ѕ": "s", "Ѕ": "s",   # ѕ Ѕ
    "ј": "j", "Ј": "j",   # ј Ј
    "Һ": "h", "һ": "h",   # Һ һ
    "Ү": "y", "ү": "y",   # Ү ү
    # Greek look-alikes (lowercase primary; NFKC leaves script intact)
    "α": "a", "Α": "a",   # α Α
    "β": "b", "Β": "b",   # β Β
    "ε": "e", "Ε": "e",   # ε Ε
    "η": "n", "Η": "h",   # η Η (η looks like n, Η like H)
    "ι": "i", "Ι": "i",   # ι Ι
    "κ": "k", "Κ": "k",   # κ Κ
    "ν": "v", "Ν": "n",   # ν Ν (ν looks like v, Ν like N)
    "ο": "o", "Ο": "o",   # ο Ο
    "ρ": "p", "Ρ": "p",   # ρ Ρ
    "τ": "t", "Τ": "t",   # τ Τ
    "υ": "u", "Υ": "y",   # υ Υ
    "χ": "x", "Χ": "x",   # χ Χ
    "μ": "u",                   # μ (mu -> u; keeps 'mu' contexts intact since the μ symbol -> 'u')
})


def _normalise(func: str) -> str:
    """Lowercase, Unicode-normalise (NFKC to fold fullwidth ASCII + compatibility characters), strip invisibles
    (Cf: zero-width space / joiner / word joiner / RLM/LRM; Mn: combining marks; Cc: control chars), fold common
    Cyrillic/Greek homoglyphs to their Latin look-alikes, then reduce punctuation to spaces and single-space-pad,
    so a membership test is whole-word/phrase and a single confusable or zero-width injection cannot bypass it."""
    # NFKC first: folds fullwidth ASCII (Ｒicin -> Ricin) and other compatibility characters
    s = unicodedata.normalize("NFKC", func)
    # Strip invisibles: Cf (format: ZWSP U+200B, ZWJ, ZWNJ, WORD JOINER, LRM, RLM),
    # Mn (nonspacing combining marks), Cc (control). These render as nothing but split tokens.
    s = "".join(c for c in s if unicodedata.category(c) not in ("Cf", "Mn", "Cc"))
    # Fold Cyrillic/Greek homoglyphs to Latin (must be BEFORE the [a-z0-9-] filter, which would drop them)
    s = s.translate(_CONFUSABLES)
    s = s.lower()
    flat = "".join(c if c in _WORD_CHARS else " " for c in s)
    return " " + " ".join(flat.split()) + " "


def _listed_select_toxin(func: str) -> str | None:
    """A listed select-agent toxin named DIRECTLY. Whole-word matched, so 'ricinus' is not read as 'ricin'; the
    Greek-letter-prefix case (omega-conotoxin, alpha-conotoxin, mu-conotoxin) matches at a hyphen boundary
    because that is how conotoxins are named in the primary literature."""
    f = _normalise(func)
    for t in sorted(SELECT_AGENT_TOXINS):
        # standalone token, or attached at a hyphen boundary (alpha-conotoxin / conotoxin-i-like)
        if " " + t + " " in f or "-" + t + " " in f or " " + t + "-" in f:
            return t
    return None


def _has_unnegated_descriptor(f: str, descriptors) -> bool:
    """True iff any descriptor appears in f NOT immediately preceded by a negator token. A -free / -negative
    suffix on the descriptor's own token already fails whole-word match (e.g. 'toxin-free' normalises to one
    hyphen-bound token), so no extra guard is needed for that shape."""
    for d in descriptors:
        needle = " " + d + " "
        pos = f.find(needle)
        while pos >= 0:
            before = f[:pos].rstrip()
            prev = before.rsplit(" ", 1)[-1] if before else ""
            if prev not in _NEGATORS:
                return True
            pos = f.find(needle, pos + 1)
    return False


def _indirect_select_toxin(func: str) -> tuple[str, str] | None:
    """A listed select-agent toxin named INDIRECTLY: a source organism together with a toxin descriptor, rather than
    the listed name. Both parts are required, so naming the organism on its own is not screened, and a scope
    disclaimer ('no toxin', 'without toxin') is not read as an affirmative descriptor.

    Returns (organism, kind) where kind is 'strong' (definitive: refuse) or 'ambiguous' (agglutinin/lectin:
    refuse UNLESS a distinct-non-select lectin marker like RCA-I is present, in which case the caller downgrades)."""
    f = _normalise(func)
    has_strong = _has_unnegated_descriptor(f, _TOXIN_DESCRIPTORS_STRONG)
    has_ambig = _has_unnegated_descriptor(f, _TOXIN_DESCRIPTORS_AMBIGUOUS)
    if not (has_strong or has_ambig):
        return None
    org = next((o for o in sorted(SELECT_AGENT_TOXIN_ORGANISMS) if " " + o + " " in f), None)
    if org is None:
        return None
    return (org, "strong" if has_strong else "ambiguous")


def _has_non_select_lectin_marker(func: str) -> bool:
    """True if the cargo names an explicit distinct-non-select lectin identifier (RCA-I / RCA120 / mannose-binding
    lectin), which downgrades a Ricinus+lectin/agglutinin indirect hit from refuse to flag_for_review."""
    f = _normalise(func)
    return any(" " + m + " " in f or "-" + m + " " in f for m in _NON_SELECT_LECTIN_MARKERS)


@lru_cache(maxsize=4096)
def _guardian(func: str) -> tuple[str, str] | None:
    """(decision, reason) from the PEN-STACK Guardian for a cargo function, or None if unavailable. Cached:
    identical cargo functions (the common case - a fixed cassette across many loci) screen once."""
    try:
        from pen_stack.safety import safety_gate
        v = safety_gate({"cargo_function": func}, actor="biofirewall")
        return (getattr(v, "decision", "clear"), getattr(v, "reason", None) or "Guardian signature screen")
    except Exception:  # noqa: BLE001 - Guardian unavailable -> fall through (never crash)
        return None


def screen_cargo(plan: dict) -> Finding:
    cargo = plan.get("cargo") or {}
    func = str(cargo.get("function") or plan.get("intent") or "")
    seq = cargo.get("sequence")
    got = _guardian(func)
    prov = {"source": "PEN-STACK Guardian (Pfam/InterPro + Select-Agent 42CFR73/7CFR331/9CFR121 + Australia-Group)"}
    if got is not None and got[0] == "refuse":
        return finding("hard_reject", "cargo.select_agent_or_toxin", "cargo", got[1], provenance=prov)
    # Defense in depth, and BEFORE the Guardian's lesser verdicts: a listed toxin must not be downgraded to a flag or
    # a clear because the Guardian is absent or the hazard was named indirectly.
    listed = _listed_select_toxin(func)
    if listed is not None:
        return finding("hard_reject", "cargo.select_agent_or_toxin", "cargo",
                       f"cargo declares a listed select-agent toxin ({listed})", provenance={"source": _LIST_PROV})
    indirect = _indirect_select_toxin(func)
    if indirect is not None:
        org, kind = indirect
        # An ambiguous descriptor (agglutinin/lectin) with an explicit non-select lectin identifier (RCA-I /
        # RCA120 / mannose-binding lectin) is the legitimate-reagent case: route to review, not hard-reject.
        # A definitive descriptor (toxin/neurotoxin/etc.) or an ambiguous descriptor WITHOUT the marker is the
        # covert-naming case: hard-reject.
        if kind == "ambiguous" and _has_non_select_lectin_marker(func):
            return finding("scope_flag", "cargo.select_agent_ambiguous_lectin", "cargo",
                           f"cargo names {org} with an ambiguous lectin/agglutinin descriptor and a distinct "
                           "non-select lectin identifier (e.g. RCA-I / RCA120 / mannose-binding lectin); routed to "
                           "human review because the coupling to a listed toxin warrants oversight",
                           provenance={"source": _LIST_PROV})
        return finding("hard_reject", "cargo.select_agent_indirect_name", "cargo",
                       f"cargo names a listed select-agent toxin indirectly, by source organism ({org}) plus a "
                       "toxin descriptor, rather than by its listed name", provenance={"source": _LIST_PROV})
    if got is not None:
        d, reason = got
        if d == "escalate":
            return finding("scope_flag", "cargo.dual_use_escalate", "cargo",
                           reason + " - ambiguous dual-use (e.g. gain-of-function) routed to oversight (P3CO/DURC)", provenance=prov)
        if d == "flag":
            return finding("soft_penalty", "cargo.flag", "cargo", reason, provenance=prov)
    if any(t in func.lower() for t in ("gene drive", "gene_drive", "homing endonuclease drive")):
        return finding("hard_reject", "cargo.gene_drive", "cargo",
                       "self-propagating gene-drive cassette in a releasable context")
    # function-aware ML: a cargo SEQUENCE whose ESM2 embedding leans toxin (low-identity homolog) -> route to review.
    score, available = function_aware_score(seq)
    if available and score is not None and score > 0.02:
        return finding("scope_flag", "cargo.function_aware_ml", "cargo",
                       f"function-aware ESM2 screen flags a toxin-leaning cargo (lean-score {score:+.3f}) that may evade "
                       "signature/homology screens - route to review",
                       provenance={"source": "ESM2 nearest-centroid (public toxin/benign refs)"}, score=score, extrapolating=True)
    return finding("clear", None, "cargo", "no cargo hazard signature")
