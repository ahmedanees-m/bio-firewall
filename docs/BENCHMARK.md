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
plainly as a limitation of data-membership calibration. **→ v0.4.0 resolves this with a competence-conditioned,
conformal calibration in Benchmark 4b below.**

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
compositional**; we do not claim a clean win. (Component-level novelty is not claimed either — cf. ToxDL [Pan 2020]
/ OmniTox [Mathew 2025, PMC12699701]; the contribution is the governed five-axis integration + this honest
benchmark.) **→ v0.4.0 follows this confound to ground
in Benchmark 2b below.**

---

# v0.4.0 — "The Hardened Core" (pre-registered: `prereg/ws_biofirewall.yaml::upgrade_v04_v10`)

v0.4.0 hardens the two load-bearing things before manuscript drafting: it follows the composition confound under
Benchmark 2 to ground (2b), and converts the *inverted* calibration of Benchmark 4 into a certified false-refuse
ceiling + a monotone confidence (4b). Both pre-registered criteria carry a **pre-committed honest-failure path**.

## Benchmark 2b — composition-decorrelation (WS-CARGO-DECORR), seed 1234

Is the cargo ESM2 signal **function-driven** or just the amino-acid-**composition** shortcut Benchmark 2 flagged
(composition probe AUROC 0.93 / TPR@1%FPR 0.562)? We reuse the frozen Benchmark-2 vectors and add three lines of
evidence. Code: [`bio_firewall/eval/cargo_bench/decorr.py`](../bio_firewall/eval/cargo_bench/decorr.py). Held-out
≤40%-id test set: **482 toxin positives / 362 benign negatives**.

| full ≤40%-id test set | TPR@1%FPR | **TPR@5%FPR** | AUROC |
|---|:--:|:--:|:--:|
| ESM head (original) | 0.716 (CI .46–.89) | **0.965** (CI .86–.99) | 0.988 (CI .978–.995) |
| **ESM head — composition-INVARIANT (DANN)** | 0.539 (CI .02–.91) | **0.967** (CI .83–.99) | **0.985** (CI .973–.993) |
| composition-only probe | 0.562 (CI .12–.74) | 0.768 (CI .54–.90) | 0.930 (CI .886–.961) |

- **Composition is GENUINELY SEPARABLE from toxins** — even bidirectional common-support matching cannot build a
  composition-matched benign set from the pool (energy-distance permutation *p* < 0.05 on the tight overlap region).
  So the confound is real: toxins (e.g. cysteine-rich) have distinctive composition.
- **The pre-registered TPR@1%FPR gate is UNDERPOWERED and does NOT pass.** With only 362 held-out negatives, the
  1%-FPR threshold rests on ~3–4 proteins, so all three heads' CIs span ~0.0–0.9; the paired (DANN−composition)
  TPR@1%FPR difference is −0.005 (CI −0.57…+0.52) — the operating-point question is simply not adjudicable here.
- **The POWERED adjudication is AUROC and TPR@5%FPR**, and it is decisive: a **composition-INVARIANT** representation
  (gradient-reversal DANN, trained to *discard* composition) retains **AUROC 0.985** and **TPR@5%FPR 0.967** — vs the
  composition probe's 0.930 / 0.768 — with the **paired AUROC difference +0.054 (CI 0.025…0.099, excludes 0)**.
  Decorrelation costs only ~0.003 AUROC. **The cargo signal is substantially NON-COMPOSITIONAL in its ranking.**

**Verdict (honest-failure path, pre-committed):** the function-aware signal is real and substantially
non-compositional (AUROC + TPR@5%FPR), but the strict **1%-FPR operating-point** advantage over a composition
baseline is **not** statistically established on this held-out set. Per the pre-registration we therefore **demote
C** from "cleanest claim": the manuscript leads on **D + the operational properties**, reporting the cargo gate as
*AUROC-level non-compositional with an explicit 1%-FPR operating-point caveat*. We did **not** tune the matched set to
rescue the margin. (Per-residue attribution is declared supporting future detail; the powered AUROC/TPR@5%FPR
decorrelation is the primary evidence.)

## Benchmark 4b — conformal calibration + false-refuse certificate (WS-CONFORMAL), seed 1234

Benchmark 4 reported an *inverted* tier accuracy. v0.4.0 replaces it with (i) a **certified** Neyman-Pearson
false-refuse ceiling and (ii) a **competence-conditioned** confidence that is monotone in correctness. Code:
[`bio_firewall/calibrate/conformal.py`](../bio_firewall/calibrate/conformal.py) +
[`eval/hazard_bench/conformal_bench.py`](../bio_firewall/eval/hazard_bench/conformal_bench.py). Corpus: the
Benchmark-1 independent-label universe (n=1496) + an **expanded legitimate-research set (n=288)** of hazard-adjacent
plans (real cancer-gene knockouts, deletion screens, a mouse germline model) that MUST flag, not refuse.

**(i) False-refuse certificate — the operational moat (vs head-to-head claim D).** The firewall refuses **0 / 288**
legitimate-research plans → a **Clopper-Pearson 95% upper bound of 0.0103** on P(refuse | legitimate research):

| target α | empirical false-refuse | certified upper bound | pass (≤ α + 0.02)? |
|---|:--:|:--:|:--:|
| 0.01 | 0.000 | **0.0103** | ✅ |
| 0.05 | 0.000 | 0.0103 | ✅ |
| 0.10 | 0.000 | 0.0103 | ✅ |

This is exactly the guarantee a jailbroken / over-refusing LLM judge **cannot** offer (D: open judges flip
`refuse→allow` 50–83% under injection; a frontier LLM over-refuses legitimate research 40%).

**(ii) Competence-conditioned confidence resolves the inversion.** A clean `allow` is high-confidence *only* when the
gene is inside the firewall's knowledge base; an **out-of-coverage** allow (the competence boundary, where the misses
live) is honestly **low** confidence. On a held-out gene split:

| confidence tier | n | empirical accuracy |
|---|:--:|:--:|
| high | 248 | **1.000** |
| moderate | 490 | 0.686 |
| low | 10 | **0.100** (9/10 are real misses — correctly flagged uncertain) |

Monotone **high > moderate > low** ✅ (the v0.3 scheme was *uninformative* on this split — allow-tier 0.782 ≈
flag-tier 0.782). Coverage breakdown: 610 in-KB / 869 constraint-only / 17 out-of-KB. The selective-abstention curve
(continuous risk = severity + continuous gnomAD pLI) reports the achievable miss-rate vs benign-escalation Pareto.

**Gate: PASS** — certified false-refuse ceiling for α∈{.01,.05,.10}, and the calibrated confidence is monotone in
correctness. (Honest limit retained: the firewall's confident misses are out-of-distribution genes it has no feature
for; the low tier *flags* this boundary, it does not eliminate it.)

---

## Reproduce

```bash
pip install -e .                                  # + pen-stack>=6.6.0
export PEN_STACK_HOME=/path/to/pen-stack          # Guardian configs (for B0 / cargo axis)
export BF_BENCH_ORACLES=/path/to/bench_oracles    # local-only COSMIC etc. (NOT in this repo)
export BF_B1_VERDICTS=/path/to/b1_verdicts.json   # optional frontier-reviewer verdicts
python -m bio_firewall.eval.hazard_bench.run_all                              # Benchmarks 1, 3, 4

# v0.4.0 — Benchmark 4b (conformal calibration + false-refuse certificate)
python -c "from bio_firewall.eval.hazard_bench import conformal_bench as c; import json; print(json.dumps(c.run()['gate'], indent=2))"

# v0.4.0 — Benchmark 2b (composition-decorrelation); needs the frozen Benchmark-2 vectors + the ml extra (torch)
BF_B2_DIR=/path/to/bf_b2 python -c "from bio_firewall.eval.cargo_bench import decorr; import json; print(json.dumps(decorr.run()['gate'], indent=2))"
```

Tier-1 is committed (public literature facts). COSMIC and the run artifacts are **local-only** — without them the
harness runs Tier-1 + the negative set and reports what it can, skipping the COSMIC strata. Benchmark 2b reuses the
frozen Benchmark-2 vectors (`bf_b2/`, local-only — vectors + public-proxy sequences, never committed).

## What this does and does not prove

It measures **concordance with an independent hazard model and the lift over real baselines** — it does **not**
measure prevented harm. A frontier LLM is a strong locus baseline; the firewall's value is determinism,
flag-not-block usability, auditability, and the non-locus axes + cargo ML. Concordance is **necessary, not
sufficient**, for real-world safety, which awaits wet-lab validation (declared future work).
