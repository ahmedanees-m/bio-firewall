# BioFirewall — Benchmark (de-circularized) results

> The v0.3 demo reported "100% vs 0%." That number was **tautological**: the homology baseline was a hardcoded
> `return "allow"`, and the proxies named the exact genes the rules target. This page reports the **real**
> benchmark — de-circularized, with earned baselines, powered, and honest — per
> `Final_Part_v3.0/Biofirewall/BIOFIREWALL_BENCHMARK_PROTOCOL_v1.0.md`. Code: [`bio_firewall/eval/hazard_bench/`](../bio_firewall/eval/hazard_bench).

## The de-circularization principle

The firewall flags loci using **CancerMine + DepMap + gnomAD** (its vendored data). The benchmark therefore **labels**
hazard from sources the firewall *does not use*, so a high score means the firewall **generalized** to an independent
definition of hazard — not that it recognized its own gene list:

- **Tier-1 (gold, mandatory):** 12 hand-curated genes near which vector integration caused **actual clonal
  expansion / leukemia / MDS in human gene-therapy trials** (SCID-X1, WAS, CGD, β-thal) — measured harm, with DOIs.
- **Tier-2 (broad):** the **COSMIC Cancer Gene Census v104** (768 expert-curated cancer genes) — an independent
  census, *license-restricted*, loaded **local-only** and **never committed** (a CI test enforces no restricted
  data enters the repo).

Baselines are **earned, not hardcoded**: **B0** runs the actual PEN-STACK Guardian signature screen on the cargo
(blind to where/how/inheritance/scale); **B1** is a current frontier model (`claude-opus-4-8`, 2026-06-17) acting as
a blind safety reviewer with a neutral pinned prompt (no firewall axes leaked) — the key comparison.

## Benchmark 1 — structural-hazard interception (locus axis), seed 1234, n = 771

| stratum | n | firewall | B0 homology | B1 frontier |
|---|---|---|---|---|
| **tier1_gold** (clinical CIS) | 12 | **100%** ✅ | 0% | 100% |
| cosmic_overlap | 509 | 100% | 0% | 94% |
| cosmic_generalization | 250 | **40%** (CI 0.33–0.46) | 0% | 50% |
| **overall** | 771 | **80.4%** (CI 0.776–0.831) | **0.0%** | 77.3%¹ |

¹ B1 measured on the pre-registered stratified sample (n = 142; 75 hazardous).

**The honest reading:**
- The homology / synthesis-screen floor (**B0**) catches **0%** of these structural-locus hazards (the cargo is
  benign — there is nothing for a sequence screen to see). **The design-stage gap is real.**
- A **frontier LLM (B1) is a strong locus-recall baseline** — 77.3% vs the rule firewall's 74.7% on the same
  sample; it even edges the firewall on the obscure *generalization* genes. So the honest answer to "can a smart LLM
  catch structural hazards by reasoning?" is, for the **locus** axis, **largely yes**.
- **But the firewall wins decisively where deployment matters:** on declared legitimate-research plans, the firewall
  **never blocks** (false-refuse **0/5**), while the frontier model **refused** legitimate TP53 and APC knockout
  cancer-modeling research (**2/5**). The firewall flags-for-review with evidence; it does not stop the lab.
- The firewall's contribution on the locus axis is therefore **deterministic, stratified (flag-not-block), auditable**
  governance with near-zero false-refuse — **not** a claim of higher raw recall than a frontier model.

**Usability (Claim C):** false-refuse on legitimate research **0%** (deployment gate); false-flag on clearly-benign
genes **6.8%**; dosage-sensitive negatives 120/120 flagged correctly, 0 wrongly refused.

**Failure analysis (honest):** the firewall **misses 151 COSMIC genes** (20%) that are absent from its CancerMine
data and not caught via the essential/dosage axes — the real generalization limit, reported rather than hidden.

## Benchmark 1b — two independent censuses (COSMIC + OncoKB)

To show the 80% is not an artifact of one curation, the firewall is scored against a **second** independent cancer-gene
census — **OncoKB** (844 genes; license-restricted, local-only, never committed) — which the firewall also does not use.
COSMIC and OncoKB are genuinely different curations (455 overlap; 313 COSMIC-only, 389 OncoKB-only).

| firewall recall vs | recall | n |
|---|:--:|:--:|
| COSMIC (+Tier-1) | 80.4% | 771 |
| OncoKB (+Tier-1) | 82.0% | 848 |
| union | 78.0% | 1160 |
| **consensus** (genes *both* censuses call cancer genes) | **89.2%** | 455 |
| — OncoKB-only genes | 73.3% | 389 |
| — COSMIC-only genes | 67.4% | 313 |

**Reading:** recall is **consistent across two independent censuses** (80% / 82%), highest on the **consensus** genes
both agree on (**89.2%**), and lower on the contested single-census genes (67–73%) — exactly the shape an honest
generalization should have. The firewall is most reliable on well-established cancer genes and weaker on niche/contested
ones; that gradient is reported, not hidden.

## Benchmark 3 — robustness / red-team

46 systematic attacks across four evasion families (reframing, prompt-injection, obfuscation, combined
frontier-orchestration) against the firewall's high-severity `refuse` decisions (select-agent cargo, gene-drive,
human heritable clinical edit, oncogenic fusion):

- **flip-rate `refuse → allow` = 0%**, grounding-under-injection violations = **0** → **PASS**. The artifact decides,
  not the framing.

## Benchmark 4 — calibration (honest, not conformal)

Against the independent labels: tier accuracy **high = 0.789, moderate = 0.938** — *inverted*. This is an honest
finding, not a failure: the firewall's confidence reflects **which axis fired** (deterministic vs mechanism), **not**
its epistemic uncertainty against an external label, so its "high-confidence allows" include **confident misses** of
COSMIC genes absent from its data. Abstention cannot rescue confident misses (hazard-miss 19.6% either way). Stated
plainly as a limitation of data-membership calibration.

## Benchmark 2 — cargo function-aware ML (the pre-registered gate)

ESM2-650M embeddings + a logistic head vs a homology baseline on **MMseqs2 ≤40%-identity held-out clusters** (no test
protein has a >40%-id neighbour in training — the "never-before-seen homolog" setting). Public UniProt toxins
(KW-0800, reviewed) vs benign non-toxin, length 50–500; 1556 train / 844 test over 1482 clusters (444 held out).
Code: [`bio_firewall/eval/cargo_bench/`](../bio_firewall/eval/cargo_bench). Ship **vectors only**.

| | TPR@1%FPR | AUROC | FPR@95%TPR |
|---|:--:|:--:|:--:|
| **ESM2-650M head** | **0.72** (CI 0.43–0.89) | **0.988** | 0.041 |
| homology baseline | 0.207 | 0.823 | — |
| *shortcut: composition* | *0.562* | *0.93* | — |
| *shortcut: length* | *0.131* | *0.862* | — |

**Gate: PASS** — the ESM head beats homology **3.5×** at the 1%-FPR deployment point, CI excluding the baseline. On
≤40%-identity held-out clusters a homology screen is weak *by construction* (that is the whole point of function-aware
screening), and the embedding recovers most of the lost signal.

**Honest caveat (must be stated):** the **amino-acid-composition shortcut probe reaches AUROC 0.93 / TPR@1%FPR 0.562** —
toxins have distinctive composition (e.g. cysteine-rich), so composition is a **strong confound**. The ESM head still
beats it (0.72 > 0.562 at the operating point; AUROC 0.988 > 0.93), so there is genuine signal **beyond** composition —
but the margin over a trivial composition baseline is modest. The function-aware advantage is **real but partly
compositional**; we do not claim a clean win. (Component-level novelty is not claimed either — cf. ToxDL/Omnyra; the
contribution is the governed five-axis integration + this honest benchmark.)

## Reproduce

```bash
pip install -e .                                  # + pen-stack>=6.6.0
export PEN_STACK_HOME=/path/to/pen-stack          # Guardian configs (for B0 / cargo axis)
export BF_BENCH_ORACLES=/path/to/bench_oracles    # local-only COSMIC etc. (NOT in this repo)
export BF_B1_VERDICTS=/path/to/b1_verdicts.json   # optional frontier-reviewer verdicts
python -m bio_firewall.eval.hazard_bench.run_all
```

Tier-1 is committed (public literature facts). COSMIC and the run artifacts are **local-only** — without them the
harness runs Tier-1 + the negative set and reports what it can, skipping the COSMIC strata.

## What this does and does not prove

It measures **concordance with an independent hazard model and the lift over real baselines** — it does **not**
measure prevented harm. A frontier LLM is a strong locus baseline; the firewall's value is determinism,
flag-not-block usability, auditability, and the non-locus axes + cargo ML. Concordance is **necessary, not
sufficient**, for real-world safety, which awaits wet-lab validation (declared future work).
