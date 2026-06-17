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

## Benchmark 2 — cargo function-aware ML (the pre-registered gate) — *pending*

ESM2-650M head vs a homology baseline on MMseqs2 ≤40%-identity held-out clusters (TPR@1%FPR, FPR@95%TPR, AUROC +
length/composition/taxonomy shortcut probes). Runs on a GPU; see `bio_firewall/eval/cargo_bench/`.

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
