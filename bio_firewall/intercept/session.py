"""WS-DECOMP (v0.5.0) — the session-level decomposition aggregator. The per-artifact screen (spine.screen) is
blind to a hazard SPLIT across N individually-passing calls — the ABC-Bench fragment-design threat (arXiv:2606.11150):
an agent decomposes a flagged plan into sub-plans that each pass, then assembles the pieces downstream. This monitor
holds per-call facets for a session/project (LOCAL-ONLY — no plan content leaves the boundary; the P7 hash-chained
audit log carries the tamper-evident decision record) and screens the AGGREGATE for what no single call reveals.

Three aggregators:
  1. ASSEMBLY/JUNCTION inference — cargo fragments across calls that reassemble (Gibson terminal homology or
     Golden-Gate Type-IIS overhangs) into ONE construct that per-fragment screening could never see.
  2. CUMULATIVE SCALE — sum bp / edit-count / genome fraction across calls and trip the scale axis on the aggregate
     (e.g. 12 calls each deleting 150 kb are each < 1 Mb, but together restructure 1.8 Mb).
  3. COORDINATED LOCI — a session that systematically targets many distinct genotoxic-CIS / oncogene loci is a
     coordinated insertional-oncogenesis program even if each call is individually defensible.

HONESTY: this is a NECESSARY-not-sufficient defence. Assembly inference catches the overlap/Type-IIS decompositions
it models; a novel obfuscation can still evade it (reported as residual in the red-team). It FLAGS for review — it
does not claim to reconstruct intent."""
from __future__ import annotations

from bio_firewall.data import gene_roles
from bio_firewall.hazard.finding import Finding, finding
from bio_firewall.hazard.locus import _GENOTOXIC_CIS
from bio_firewall.hazard.scale import screen_scale

MIN_GIBSON_OVERLAP = 20                                  # bp of terminal homology for a Gibson-style junction
TYPE_IIS = {"BsaI": "GGTCTC", "BsmBI": "CGTCTC", "BbsI": "GAAGAC"}   # Golden-Gate recognition sites
_COMP = str.maketrans("ACGTacgt", "TGCAtgca")


def _revcomp(s: str) -> str:
    return s.translate(_COMP)[::-1]


def _facets(plan: dict) -> dict:
    """Extract the decomposition-relevant facets from a normalized plan."""
    cargo = plan.get("cargo") or {}
    edit = plan.get("edit") or {}
    scale = plan.get("scale") or {}
    seq = (cargo.get("sequence") or "").upper().replace(" ", "")
    bp = int(scale.get("total_bp") or edit.get("deleted_bp") or edit.get("inserted_bp") or len(seq) or 0)
    n_edits = int(scale.get("n_edits") or (1 if (edit or seq or cargo.get("function")) else 0))
    return {"sequence": seq, "bp": bp, "n_edits": n_edits,
            "intent": str(plan.get("intent") or ""), "gene": str((plan.get("locus") or {}).get("gene") or "").upper(),
            "function": str(cargo.get("function") or "")}


# --------------------------------------------------------------------------------------------------------------
# 1. assembly / junction inference
# --------------------------------------------------------------------------------------------------------------
def _overlap(a: str, b: str) -> int:
    """Longest k where suffix(a,k) == prefix(b,k) (k <= 40), else 0 — a Gibson/SLIC homology junction."""
    m = min(len(a), len(b), 40)
    for k in range(m, MIN_GIBSON_OVERLAP - 1, -1):
        if a[-k:] == b[:k]:
            return k
    return 0


def reassemble(fragments: list[str]) -> list[dict]:
    """Greedy junction-graph assembly over cargo fragments (forward + reverse-complement). Returns the maximal
    multi-fragment chains (>=2 fragments) that reassemble via Gibson homology or a shared Type-IIS site — the
    constructs per-fragment screening is blind to."""
    frags = [f for f in fragments if f and len(f) >= MIN_GIBSON_OVERLAP]
    oriented = frags + [_revcomp(f) for f in frags]
    used: set[int] = set()
    chains: list[dict] = []
    for i, fi in enumerate(oriented[:len(frags)]):          # seed from forward fragments only
        if i in used:
            continue
        chain, seq, members = [i], fi, {i % len(frags)}
        extended = True
        while extended:
            extended = False
            for j, fj in enumerate(oriented):
                base = j % len(frags)
                if base in members:
                    continue
                ov = _overlap(seq, fj)
                if ov:
                    seq += fj[ov:]
                    chain.append(j)
                    members.add(base)
                    used.add(j % len(frags))
                    extended = True
                    break
        if len(members) >= 2:
            used.update(members)
            chains.append({"n_fragments": len(members), "assembled_length": len(seq),
                           "junction": "gibson_homology", "assembled_sequence": seq})
    # Type-IIS (Golden-Gate): real parts carry the SAME enzyme's site near a TERMINUS (it cuts outside itself to
    # leave the assembly overhang). Require terminal proximity + a MAJORITY of fragments — internal 6-bp matches in
    # random DNA are coincidental and must NOT trip this (the red-team measures the false-positive rate).
    def _terminal_site(f: str, site: str, win: int = 30) -> bool:
        ends = (f[:win] + " " + f[-win:]).upper()
        rc = (_revcomp(f[:win]) + " " + _revcomp(f[-win:])).upper()
        return site in ends or site in rc
    for name, site in TYPE_IIS.items():
        n = sum(1 for f in frags if _terminal_site(f, site))
        if n >= 2 and n >= (len(frags) + 1) // 2:
            chains.append({"n_fragments": n, "junction": f"type_IIS_{name}", "assembled_length": None,
                           "assembled_sequence": None})
    return chains


def assembly_finding(fragments: list[str]) -> Finding | None:
    chains = reassemble(fragments)
    if not chains:
        return None
    biggest = max(chains, key=lambda c: c["n_fragments"])
    return finding("scope_flag", "session.covert_multifragment_assembly", "scale",
                   f"{biggest['n_fragments']} cargo fragments across separate calls reassemble into one construct "
                   f"({biggest['junction']}) — per-fragment screening is blind to the assembled whole; screen it",
                   provenance={"source": "session decomposition aggregator (Gibson/Type-IIS junction inference)"},
                   extrapolating=True)


# --------------------------------------------------------------------------------------------------------------
# 2. cumulative scale
# --------------------------------------------------------------------------------------------------------------
def cumulative_scale_finding(facets: list[dict]) -> Finding | None:
    bp = sum(f["bp"] for f in facets)
    n_edits = sum(f["n_edits"] for f in facets)
    agg = screen_scale({"scale": {"total_bp": bp, "n_edits": n_edits}})
    if agg.decision == "clear":
        return None
    return finding(agg.decision, "session." + (agg.rule_id or "cumulative_scale").split(".")[-1], "scale",
                   f"cumulative across {len(facets)} calls: {bp:,} bp / {n_edits} edits — {agg.mechanism} "
                   "(no single call crossed the threshold)", extrapolating=True)


# --------------------------------------------------------------------------------------------------------------
# 3. coordinated loci
# --------------------------------------------------------------------------------------------------------------
def coordinated_loci_finding(facets: list[dict], threshold: int = 3) -> Finding | None:
    hot = sorted({f["gene"] for f in facets
                  if f["gene"] and (f["gene"] in _GENOTOXIC_CIS or (gene_roles(f["gene"]) & {"oncogene", "driver"}))})
    if len(hot) < threshold:
        return None
    return finding("scope_flag", "session.coordinated_oncogenic_loci", "locus",
                   f"session targets {len(hot)} distinct genotoxic-CIS / oncogene loci ({', '.join(hot[:6])}"
                   f"{'…' if len(hot) > 6 else ''}) — a coordinated insertional-oncogenesis pattern across calls",
                   provenance={"source": "session decomposition aggregator (coordinated-loci clustering)"},
                   extrapolating=True)


# --------------------------------------------------------------------------------------------------------------
# the monitor
# --------------------------------------------------------------------------------------------------------------
class SessionMonitor:
    """Accumulates per-call facets for a session and screens the aggregate. `observe()` each screened artifact;
    `aggregate()` returns the session-level verdict. Facets are local-only; pass an AuditLog to also record the
    per-call decision in the tamper-evident chain (no plan content stored in the audit record)."""

    def __init__(self, session_id: str = "session", audit=None):
        from bio_firewall.adapters.generic_artifact import normalize
        self.session_id = session_id
        self.audit = audit
        self._normalize = normalize
        self.facets: list[dict] = []

    def observe(self, artifact: dict, verdict: dict | None = None) -> None:
        self.facets.append(_facets(self._normalize(artifact)))
        if self.audit is not None and verdict is not None:
            self.audit.append({"session": self.session_id, "decision": verdict.get("decision"),
                               "inputs_hash": (verdict.get("passport") or {}).get("inputs_hash")})

    def aggregate(self) -> dict:
        findings = [f for f in (
            assembly_finding([x["sequence"] for x in self.facets]),
            cumulative_scale_finding(self.facets),
            coordinated_loci_finding(self.facets),
        ) if f is not None]
        from bio_firewall.hazard.combine import combine
        verdict = combine(findings) if findings else {"decision": "allow", "axes": {}, "evidence": [],
                                                      "reason": "no cross-call decomposition signal"}
        verdict["session_id"] = self.session_id
        verdict["n_calls"] = len(self.facets)
        verdict["decomposition_signals"] = [f.rule_id for f in findings]
        return verdict
