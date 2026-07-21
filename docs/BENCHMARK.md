# BioFirewall - Benchmark (de-circularized) results

> An earlier demo reported "100% vs 0%." That number was **tautological**: the homology baseline was a hardcoded
> `return "allow"`, and the proxies named the exact genes the rules target. This page reports the **real**
> benchmark: de-circularized, with earned baselines, and powered.
> Code: [`bio_firewall/eval/hazard_bench/`](../bio_firewall/eval/hazard_bench).

## The de-circularization principle

The firewall flags loci using **CancerMine + DepMap + gnomAD** (its vendored data). The benchmark therefore **labels**
hazard from sources the firewall *does not use*, so a high score means the firewall **generalized** to an independent
definition of hazard - not that it recognized its own gene list:

- **Tier-1 (gold, mandatory):** 12 hand-curated genes near which vector integration caused **actual clonal
  expansion / leukemia / MDS in human gene-therapy trials** (SCID-X1, WAS, CGD, beta-thal) - measured harm, with DOIs.
- **Tier-2 (broad):** the **COSMIC Cancer Gene Census v104** (768 expert-curated cancer genes) - an independent
  census, *license-restricted*, loaded **local-only** and **never committed** (a CI test enforces no restricted
  data enters the repo).

Baselines are **earned, not hardcoded**: **B0** runs the actual PEN-STACK Guardian signature screen on the cargo
(blind to where/how/inheritance/scale); **B1** is a current frontier model (`claude-opus-4-8`, 2026-06-17) acting as
a blind safety reviewer with a neutral pinned prompt (no firewall axes leaked) - the key comparison.

## Benchmark 1 - structural-hazard interception (locus axis), seed 1234, n = 771

| stratum | n | firewall | B0 homology | B1 frontier |
|---|---|---|---|---|
| **tier1_gold** (clinical CIS) | 12 | **100%** yes | 0% | 100% |
| cosmic_overlap | 509 | 100% | 0% | 94% |
| cosmic_generalization | 250 | **40%** (CI 0.33-0.46) | 0% | 50% |
| **overall** | 771 | **80.4%** (CI 0.776-0.831) | **0.0%** | 77.3% |

 B1 measured on the pre-registered stratified sample (n = 142; 75 hazardous).

**Interpretation:**
- The homology / synthesis-screen floor (**B0**) catches **0%** of these structural-locus hazards (the cargo is
  benign - there is nothing for a sequence screen to see). **The design-stage gap is real.**
- A **frontier LLM (B1) is a strong locus-recall baseline** - 77.3% vs the rule firewall's 74.7% on the same
  sample; it even edges the firewall on the obscure *generalization* genes. So the answer to "can a smart LLM
  catch structural hazards by reasoning?" is, for the **locus** axis, **largely yes**.
- **But the firewall wins decisively where deployment matters:** on declared legitimate-research plans, the firewall
  **never blocks** (false-refuse **0/5**), while the frontier model **refused** legitimate TP53 and APC knockout
  cancer-modeling research (**2/5**). The firewall flags-for-review with evidence; it does not stop the lab.
- The firewall's contribution on the locus axis is therefore **deterministic, stratified (flag-not-block), auditable**
  governance with near-zero false-refuse - **not** a claim of higher raw recall than a frontier model.

**Usability (Claim C):** false-refuse on legitimate research **0%** (deployment gate); false-flag on clearly-benign
genes **6.8%**; dosage-sensitive negatives 120/120 flagged correctly, 0 wrongly refused.

**Failure analysis :** the firewall **misses 151 COSMIC genes** (20%) that are absent from its CancerMine
data and not caught via the essential/dosage axes - the real generalization limit, reported rather than hidden.

## Benchmark 1b - two independent censuses (COSMIC + OncoKB)

To show the 80% is not an artifact of one curation, the firewall is scored against a **second** independent cancer-gene
census - **OncoKB** (844 genes; license-restricted, local-only, never committed) - which the firewall also does not use.
COSMIC and OncoKB are genuinely different curations (455 overlap; 313 COSMIC-only, 389 OncoKB-only).

| firewall recall vs | recall | n |
|---|:--:|:--:|
| COSMIC (+Tier-1) | 80.4% | 771 |
| OncoKB (+Tier-1) | 82.0% | 848 |
| union | 78.0% | 1160 |
| **consensus** (genes *both* censuses call cancer genes) | **89.2%** | 455 |
| - OncoKB-only genes | 73.3% | 389 |
| - COSMIC-only genes | 67.4% | 313 |

**Reading:** recall is **consistent across two independent censuses** (80% / 82%), highest on the **consensus** genes
both agree on (**89.2%**), and lower on the contested single-census genes (67-73%) - exactly the shape a generalization should have. The firewall is most reliable on well-established cancer genes and weaker on niche/contested
ones; that gradient is reported, not hidden.

## Benchmark 3 - robustness / red-team

46 systematic attacks across four evasion families (reframing, prompt-injection, obfuscation, combined
frontier-orchestration) against the firewall's high-severity `refuse` decisions (select-agent cargo, gene-drive,
human heritable clinical edit, oncogenic fusion):

- **flip-rate `refuse -> allow` = 0%**, grounding-under-injection violations = **0** -> **PASS**. The artifact decides,
  not the framing.

## Benchmark 4 - calibration (not conformal)

Against the independent labels: tier accuracy **high = 0.789, moderate = 0.938** - *inverted*. This is a finding, not a failure: the firewall's confidence reflects **which axis fired** (deterministic vs mechanism), **not**
its epistemic uncertainty against an external label, so its "high-confidence allows" include **confident misses** of
COSMIC genes absent from its data. Abstention cannot rescue confident misses (hazard-miss 19.6% either way). Stated
plainly as a limitation of data-membership calibration. **-> This is resolved with a competence-conditioned,
conformal calibration in Benchmark 4b below.**

## Benchmark 2 - cargo function-aware ML (the pre-registered gate)

ESM2-650M embeddings + a logistic head vs a homology baseline on **MMseqs2 <=40%-identity held-out clusters** (no test
protein has a >40%-id neighbour in training - the "never-before-seen homolog" setting). Public UniProt toxins
(KW-0800, reviewed) vs benign non-toxin, length 50-500; 1556 train / 844 test over 1482 clusters (444 held out).
Code: [`bio_firewall/eval/cargo_bench/`](../bio_firewall/eval/cargo_bench). Ship **vectors only**.

| | TPR@1%FPR | AUROC | FPR@95%TPR |
|---|:--:|:--:|:--:|
| **ESM2-650M head** | **0.72** (CI 0.43-0.89) | **0.988** | 0.041 |
| homology baseline | 0.207 | 0.823 | - |
| *shortcut: composition* | *0.562* | *0.93* | - |
| *shortcut: length* | *0.131* | *0.862* | - |

**Gate: PASS** - the ESM head beats homology **3.5x** at the 1%-FPR deployment point, CI excluding the baseline. On
<=40%-identity held-out clusters a homology screen is weak *by construction* (that is the whole point of function-aware
screening), and the embedding recovers most of the lost signal.

**Caveat (must be stated):** the **amino-acid-composition shortcut probe reaches AUROC 0.93 / TPR@1%FPR 0.562** -
toxins have distinctive composition (e.g. cysteine-rich), so composition is a **strong confound**. The ESM head still
beats it (0.72 > 0.562 at the operating point; AUROC 0.988 > 0.93), so there is genuine signal **beyond** composition -
but the margin over a trivial composition baseline is modest. The function-aware advantage is **real but partly
compositional**; we do not claim a clean win. (Component-level novelty is not claimed either - cf. ToxDL [Pan 2020]
/ OmniTox [Mathew 2025, PMC12699701]; the contribution is the governed five-axis integration + this benchmark.) **-> We follow this confound to ground
in Benchmark 2b below.**

---

# Cargo decorrelation and the certified false-refuse bound (pre-registered: `prereg/ws_biofirewall.yaml`)

This release hardens the two load-bearing things before manuscript drafting: it follows the composition confound under
Benchmark 2 to ground (2b), and converts the *inverted* calibration of Benchmark 4 into a certified false-refuse
ceiling + a monotone confidence (4b). Both pre-registered criteria carry a **pre-committed pre-registered fallback path**.

## Benchmark 2b - composition-decorrelation, seed 1234

Is the cargo ESM2 signal **function-driven** or just the amino-acid-**composition** shortcut Benchmark 2 flagged
(composition probe AUROC 0.93 / TPR@1%FPR 0.562)? We reuse the frozen Benchmark-2 vectors and add three lines of
evidence. Code: [`bio_firewall/eval/cargo_bench/decorr.py`](../bio_firewall/eval/cargo_bench/decorr.py). Held-out
<=40%-id test set: **482 toxin positives / 362 benign negatives**.

| full <=40%-id test set | TPR@1%FPR | **TPR@5%FPR** | AUROC |
|---|:--:|:--:|:--:|
| ESM head (original) | 0.716 (CI .46-.89) | **0.965** (CI .86-.99) | 0.988 (CI .978-.995) |
| **ESM head - composition-INVARIANT (DANN)** | 0.539 (CI .02-.91) | **0.967** (CI .83-.99) | **0.985** (CI .973-.993) |
| composition-only probe | 0.562 (CI .12-.74) | 0.768 (CI .54-.90) | 0.930 (CI .886-.961) |

- **Composition is GENUINELY SEPARABLE from toxins** - even bidirectional common-support matching cannot build a
  composition-matched benign set from the pool (energy-distance permutation *p* < 0.05 on the tight overlap region).
  So the confound is real: toxins (e.g. cysteine-rich) have distinctive composition.
- **The pre-registered TPR@1%FPR gate is UNDERPOWERED and does NOT pass.** With only 362 held-out negatives, the
  1%-FPR threshold rests on ~3-4 proteins, so all three heads' CIs span ~0.0-0.9; the paired (DANN-composition)
  TPR@1%FPR difference is -0.005 (CI -0.57...+0.52) - the operating-point question is simply not adjudicable here.
- **The POWERED adjudication is AUROC and TPR@5%FPR**, and it is decisive: a **composition-INVARIANT** representation
  (gradient-reversal DANN, trained to *discard* composition) retains **AUROC 0.985** and **TPR@5%FPR 0.967** - vs the
  composition probe's 0.930 / 0.768 - with the **paired AUROC difference +0.054 (CI 0.025...0.099, excludes 0)**.
  Decorrelation costs only ~0.003 AUROC. **The cargo signal is substantially NON-COMPOSITIONAL in its ranking.**

**Verdict (pre-registered fallback path, pre-committed):** the function-aware signal is real and substantially
non-compositional (AUROC + TPR@5%FPR), but the strict **1%-FPR operating-point** advantage over a composition
baseline is **not** statistically established on this held-out set. Per the pre-registration we therefore **demote
C** from "cleanest claim": the manuscript leads on **D + the operational properties**, reporting the cargo gate as
*AUROC-level non-compositional with an explicit 1%-FPR operating-point caveat*. We did **not** tune the matched set to
rescue the margin. (Per-residue attribution is declared supporting future detail; the powered AUROC/TPR@5%FPR
decorrelation is the primary evidence.)

## Benchmark 4b - conformal calibration + false-refuse certificate, seed 1234

Benchmark 4 reported an *inverted* tier accuracy. This release replaces it with (i) a **certified** Neyman-Pearson
false-refuse ceiling and (ii) a **competence-conditioned** confidence that is monotone in correctness. Code:
[`bio_firewall/calibrate/conformal.py`](../bio_firewall/calibrate/conformal.py) +
[`eval/hazard_bench/conformal_bench.py`](../bio_firewall/eval/hazard_bench/conformal_bench.py). Corpus: the
Benchmark-1 independent-label universe (n=1496) + an **expanded legitimate-research set (n=288)** of hazard-adjacent
plans (real cancer-gene knockouts, deletion screens, a mouse germline model) that MUST flag, not refuse.

**(i) False-refuse certificate - the operational moat (vs head-to-head claim D).** The firewall refuses **0 / 288**
legitimate-research plans -> a **Clopper-Pearson 95% upper bound of 0.0103** on P(refuse | legitimate research):

| target alpha | empirical false-refuse | certified upper bound | pass (<= alpha + 0.02)? |
|---|:--:|:--:|:--:|
| 0.01 | 0.000 | **0.0103** | yes |
| 0.05 | 0.000 | 0.0103 | yes |
| 0.10 | 0.000 | 0.0103 | yes |

This is exactly the guarantee a jailbroken / over-refusing LLM judge **cannot** offer (D: open judges flip
`refuse->allow` 50-83% under injection; a frontier LLM over-refuses legitimate research 40%).

**(ii) Competence-conditioned confidence resolves the inversion.** A clean `allow` is high-confidence *only* when the
gene is inside the firewall's knowledge base; an **out-of-coverage** allow (the competence boundary, where the misses
live) is **low** confidence. On a held-out gene split:

| confidence tier | n | empirical accuracy |
|---|:--:|:--:|
| high | 248 | **1.000** |
| moderate | 490 | 0.686 |
| low | 10 | **0.100** (9/10 are real misses - correctly flagged uncertain) |

Monotone **high > moderate > low** yes (the earlier scheme was *uninformative* on this split - allow-tier 0.782 ~
flag-tier 0.782). Coverage breakdown: 610 in-KB / 869 constraint-only / 17 out-of-KB. The selective-abstention curve
(continuous risk = severity + continuous gnomAD pLI) reports the achievable miss-rate vs benign-escalation Pareto.

**Gate: PASS** - certified false-refuse ceiling for alpha in {.01,.05,.10}, and the calibrated confidence is monotone in
correctness. (Limitation retained: the firewall's confident misses are out-of-distribution genes it has no feature
for; the low tier *flags* this boundary, it does not eliminate it.)

---

# Cross-call decomposition defence (pre-registered: `prereg/ws_biofirewall.yaml`)

## Benchmark 5 - decomposition red-team, seed 1234

The single-call red-team (Benchmark 3) cannot see a hazard **split across N calls** that each pass - the ABC-Bench
fragment-design threat ([arXiv:2606.11150](https://arxiv.org/abs/2606.11150)). The **SessionMonitor**
([`bio_firewall/intercept/session.py`](../bio_firewall/intercept/session.py)) holds per-call facets (local-only;
the P7 audit chain carries the decision record) and screens the aggregate via three aggregators: assembly/junction
inference (Gibson homology + Golden-Gate Type-IIS), cumulative scale, and coordinated-loci clustering. For each
category we synthesize attacks (a flagged plan split into passing sub-plans) and benign controls (n=60 each):

| category | catch-rate (CI) | attacks that evade per-call | false-positive | true decomposition-evasion? |
|---|:--:|:--:|:--:|:--:|
| **cumulative_scale** (>1 Mb -> sub-50 kb deletions) | **1.00** [1.0, 1.0] | **1.00** | 0.00 | yes |
| **fragment_assembly** (cargo -> Gibson/Type-IIS fragments) | **1.00** [1.0, 1.0] | **1.00** | 0.00 | yes |
| coordinated_loci (many distinct CIS/oncogene loci) | 1.00 [1.0, 1.0] | 0.00 | 0.00 | no - defense-in-depth |

**Reading:** the two **genuine** decomposition evasions (cumulative scale, fragment assembly) each defeat the
per-artifact screen (`attacks that evade per-call = 1.00`) and the session aggregator catches **100% at 0%
false-positive**. `coordinated_loci` is reported in full as **defense-in-depth, not an evasion** - those loci are
individually flagged anyway (`evade per-call = 0.00`). **Limitation:** this is *necessary, not sufficient* -
assembly inference catches the Gibson/Type-IIS junctions it models; a novel obfuscation can still evade it (a named
residual). The false-positive control matters: an earlier internal Type-IIS detector fired on chance 6-bp motifs in
random DNA (21.7% FP) and was tightened to require terminal-proximity + a fragment majority -> 0% FP.

## Benchmark 6 - locus outcome-validation, the open-data floor, seed 1234

Section 6 limit #2: the locus axis flags on *mechanism* and is **not** outcome-validated; the two gene-census benchmarks
are recall-against-curation, not validation-against-outcomes. We built the enrichment harness
([`bio_firewall/eval/hazard_bench/locus_outcome.py`](../bio_firewall/eval/hazard_bench/locus_outcome.py)) - OR/AUROC
with a gene-clustered bootstrap - and ran it on the **open-data floor: VISDB** (Viral Integration Site DataBase,
Tang et al. 2020, [10.1093/nar/gkz867](https://doi.org/10.1093/nar/gkz867); local-only, the same catalogue PEN-STACK's
genotoxicity oracle uses). Each of **127,234** integration sites (mapped to 35,047 genes) carries a **Sample type**
(tumor vs not); the test asks whether firewall-flagged loci enrich among tumor-associated sites.

| stratum | n sites | AUROC (CI) | odds ratio (CI) | gate |
|---|:--:|:--:|:--:|:--:|
| overall (HIV + HTLV) | 127,234 | 0.449 [0.442, 0.456] | 0.577 [0.533, 0.628] | no |
| HIV | 82,995 | 0.494 [0.481, 0.506] | 0.925 [0.816, 1.038] | no (null) |
| HTLV | 44,239 | 0.455 [0.443, 0.468] | 0.607 [0.532, 0.701] | no |

**Result - ACCESS-GATED PATH (pre-committed; controlled-access deferred):** the pre-registered enrichment
gate is **not met** - flagged loci are if anything slightly *depleted* among tumor-associated sites (OR < 1), and
HIV is null. **The diagnosis is the informative part:** 96% of the open "tumor" sites are **HTLV** (adult T-cell
leukemia), whose integration biology is **viral-oncoprotein-driven, not insertional-oncogenesis-at-oncogenes**;
HIV does not cause cancer by insertion either. The readily-**open** catalogues are therefore the **wrong integration
biology** to validate a *gammaretroviral* insertional-oncogenesis locus model - and the right open data (MLV/XMLV
gene-therapy sites) is too sparse in VISDB (~60 sites). So the locus axis **ships unchanged** (mechanism-flag), and
outcome-validation remains **pending** on the deferred controlled-access gammaretroviral clonal-outcome data - a
status the floor now **evidences** rather than asserts. No validated risk-model claim is made.

---

# Mechanism-based axes (move each axis from a lookup to a mechanism)

## Benchmark 7 - monotone evidence combiner

The max-severity cascade is replaced by a noisy-OR combiner `1 - prod(1-r_i)`
([`hazard/combine_mono.py`](../bio_firewall/hazard/combine_mono.py)). On a 5,000-case perturbation suite it is
**provably monotone** (adding/strengthening any finding never lowers severity) and **interaction-aware** (co-occurring
moderate signals escalate severity - a `max` is flat), while **hard-rule-exact** (any `hard_reject` -> refuse; soft
severity capped below the refuse threshold so soft signals never auto-refuse). Decisions are **identical** to the
prior cascade (`decision_matches_cascade` + the spine/full/phase15 regression); a continuous auditable `severity` is
added to the verdict. **Gate: PASS** (monotone + hard-rule-exact, verified).

## Benchmark 8 - de-novo oncogenic-fusion detection

The edit axis flagged only a 14-pair curated list. [`hazard/edit_mech.py`](../bio_firewall/hazard/edit_mech.py) adds
a de-novo **mechanism** screen (function-family, no sequences): constitutive kinase activation (a CC0 fusion-kinase
family), oncogene/driver juxtaposition (CancerMine CC0), IG/TCR super-enhancer juxtaposition - generalizing beyond
membership. Held-out label = **COSMIC TRANSLOCATION_PARTNER** pairs (local-only) absent from the curated list:

| | value |
|---|:--:|
| generalization recall on 471 off-list COSMIC pairs | **0.909** (CI 0.881-0.934) |
| recall on the 112 kinase-fusion pairs (clean signal) | **1.00** |
| benign false-positive (400 non-cancer pairs) | **0.0** (CI 0.0-0.0) |

**Gate: PASS.** recall is partly role-driven (COSMIC overlaps CancerMine); the kinase subset is the cleaner
generalization signal; a research fusion of a real oncogene legitimately flags (the FP control is non-cancer pairs).

## Benchmark 9 - positional locus resolution

A gene-membership lookup is blind to the SCID-X1/LMO2 mechanism (integration in the upstream promoter/enhancer,
activating LMO2 in trans). [`hazard/locus_pos.py`](../bio_firewall/hazard/locus_pos.py) flags an insertion in the
promoter (<=10 kb) / enhancer (<=50 kb) window of an oncogene TSS (a compact vendored `oncogene_tss.parquet` -
2,183 oncogene TSS from GENCODE x CancerMine CC0). On **140,628** real VISDB integration sites: positional flags
17,158, of which **10,834 (63%) are oncogene promoter/enhancer-proximal but NOT in an oncogene gene body** - exactly
what a membership lookup misses. **The outcome-AUROC-improvement claim is DEFERRED** (controlled-access integration-
site outcome data deferred; the open VISDB floor was the wrong virus biology) - this is a coverage count, not a
calibrated rate.

## Benchmark 10 - structural remote-homology channel - negative result at 1% FPR

[`hazard/struct_channel.py`](../bio_firewall/hazard/struct_channel.py) adds a composition-independent **fold** signal
+ a 3-signal ensemble (homology / ESM / structure) that abstains on disagreement, run via **AlphaFold-DB v6 + Foldseek
(no GPU)** on the frozen Benchmark-2 holdout.

| | TPR@1%FPR | AUROC |
|---|:--:|:--:|
| ESM-alone | 0.72 | 0.988 |
| structure-alone | 0.118 | **0.882** |
| ESM + structure (mean ensemble) | 0.197 | 0.983 |

**Gate: FAIL (pre-registered fallback path).** Incremental TPR@1%FPR (ensemble - ESM) median **-0.48**, CI [-0.76, 0.20] -
the structural channel does **not** add at the strict 1%-FPR point: the same <=40%-id cluster split that weakens
sequence-homology (0.207) makes a held-out toxin **structurally distant** from the train-toxin reference, and
short-peptide AlphaFold models are low-confidence, so a mean-ensemble dilutes ESM. **But** structure-alone AUROC
**0.882** is a real fold signal, and being **composition-free by construction** it independently corroborates the
earlier non-compositionality finding at the ranking level (a modest backstop, not at 1% FPR). The
abstain-on-disagreement works (49% abstained on ESM/structure conflicts; the kept set's ESM TPR is unchanged). The
channel + ensemble + abstention are shipped; the incremental-1%-FPR claim is reported as not met on this proxy set.

---

## Reproduce

```bash
pip install -e .                                  # + pen-stack>=0.1.0,<0.2.0
export PEN_STACK_HOME=/path/to/pen-stack          # Guardian configs (for B0 / cargo axis)
export BF_BENCH_ORACLES=/path/to/bench_oracles    # local-only COSMIC etc. (NOT in this repo)
export BF_B1_VERDICTS=/path/to/b1_verdicts.json   # optional frontier-reviewer verdicts
python -m bio_firewall.eval.hazard_bench.run_all                              # Benchmarks 1, 3, 4

# Benchmark 4b (conformal calibration + false-refuse certificate)
python -c "from bio_firewall.eval.hazard_bench import conformal_bench as c; import json; print(json.dumps(c.run()['gate'], indent=2))"

# Benchmark 2b (composition-decorrelation); needs the frozen Benchmark-2 vectors + the ml extra (torch)
BF_B2_DIR=/path/to/bf_b2 python -c "from bio_firewall.eval.cargo_bench import decorr; import json; print(json.dumps(decorr.run()['gate'], indent=2))"

# Benchmark 5 (decomposition red-team)
python -c "from bio_firewall.eval.hazard_bench import decomp_redteam as d; import json; print(json.dumps(d.run(), indent=2))"

# Benchmark 6 (locus outcome floor); needs the local VISDB + GENCODE gene coords (VM only)
BF_VISDB_DIR=/path/to/visdb BF_GENE_COORDS=/path/to/gene_coords.parquet \
  python -c "from bio_firewall.eval.hazard_bench import locus_outcome as lo; import json; print(json.dumps(lo.run_visdb()['overall'], indent=2))"

# Benchmark 7 (monotone combiner proof)
python -c "from bio_firewall.hazard.combine_mono import verify_monotone; import json; print(json.dumps(verify_monotone(), indent=2))"
# Benchmark 8 (de-novo fusion generalization); needs COSMIC TRANSLOCATION_PARTNER (local)
BF_BENCH_ORACLES=/path/to/bench_oracles python -c "from bio_firewall.eval.hazard_bench import edit_mech_bench as b; import json; print(json.dumps(b.run(), indent=2))"
# Benchmark 9 (positional locus coverage); needs VISDB + gene coords (VM)
BF_VISDB_DIR=... BF_GENE_COORDS=... python -c "from bio_firewall.eval.hazard_bench import locus_pos_bench as b; import json; print(json.dumps(b.run_visdb(), indent=2))"
# Benchmark 10 (structural channel); needs AlphaFold-DB structures + Foldseek + the frozen B2 vectors (VM)
# (see scratch/run_struct_vm.py - AF-DB v6 fetch + Foldseek easy-search -> struct_bench)
```

Tier-1 is committed (public literature facts). COSMIC and the run artifacts are **local-only** - without them the
harness runs Tier-1 + the negative set and reports what it can, skipping the COSMIC strata. Benchmark 2b reuses the
frozen Benchmark-2 vectors (`bf_b2/`, local-only - vectors + public-proxy sequences, never committed).

## What this does and does not prove

It measures **concordance with an independent hazard model and the lift over real baselines** - it does **not**
measure prevented harm. A frontier LLM is a strong locus baseline; the firewall's value is determinism,
flag-not-block usability, auditability, and the non-locus axes + cargo ML. Concordance is **necessary, not
sufficient**, for real-world safety, which awaits wet-lab validation (declared future work).
