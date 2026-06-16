# BioFirewall — Hazard Taxonomy (implementation status)

Authoritative taxonomy: `BIOFIREWALL_BLUEPRINT_v0.4_FINAL.md` §3 (five axes; each with hazard / differentiating? /
signals / data / rules / scope). This file tracks the v0.1 implementation status.

| Axis | v0.1 (Phase 0) | Phase-1 work |
|---|---|---|
| **1 Cargo** | reuses PEN-STACK Guardian (Pfam/InterPro + Select-Agent + Australia-Group); gene-drive keyword stub | function-aware ML (ESM, homology-clustered ≤40%-id eval + shortcut probes); real gene-drive architecture |
| **2 Locus** *(the edge)* | genotoxic-CIS (LMO2/MECOM/…) + oncogene-activation-by-design flags | wire PEN-STACK site-safety classifier + genotox proxy; explicit TSG-disruption / dosage (DepMap, gnomAD pLI/LOEUF, ClinGen) / enhancer-hijack rules on CancerMine (CC0) |
| **3 Edit-type** | oncogenic-fusion (hard_reject) / multiplex-translocation / large-deletion | open/literature-curated fusion set; deleted-span gene-content join (GENCODE) |
| **4 Germline** | **fully implemented** — human heritable clinical → refuse; embryo/germ-cell research → scope_flag; enhancement → soft_penalty | curated germline-vs-somatic cell-type ontology expansion |
| **5 Scale** | Mb-restructuring / high-multiplex amplifier (widen intervals, lower abstention) | apply Axes 2–3 across all affected regions |

Every axis returns a `Finding(decision, rule_id, axis, mechanism, provenance, score, extrapolating)`; `combine()`
stratifies: any `hard_reject` → **refuse**; else any `soft_penalty`/`scope_flag` → **flag_for_review** (+ evidence);
else **allow** (+ passport seed). Stratification, not a blocklist; legality ≠ confidence.
