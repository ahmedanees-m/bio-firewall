# BioFirewall

**A rule-governed, genome-writing-native biosecurity layer that supervises agentic design AI.**

BioFirewall sits between a DNA-design AI and the DNA synthesizer. It inspects the *plan* the AI produced, not
only the final sequence, and returns one of **`allow`**, **`flag_for_review`**, or **`refuse`**, with cited
evidence and a signed design passport. It is the missing design-stage guardrail: a firewall for genome writing.

[![CI](https://github.com/ahmedanees-m/bio-firewall/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmedanees-m/bio-firewall/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-165%20passing%2C%202%20skipped-success.svg)
![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
[![Container](https://img.shields.io/badge/ghcr.io-bio--firewall%3A0.1.0-blue.svg)](https://github.com/ahmedanees-m/bio-firewall/pkgs/container/bio-firewall)
![pen-stack](https://img.shields.io/badge/pen--stack-0.1.0-blue.svg)
[![RRID](https://img.shields.io/badge/RRID-SCR__028785-8A2BE2.svg)](https://scicrunch.org/resolver/RRID:SCR_028785)
[![bio.tools](https://img.shields.io/badge/bio.tools-bio--firewall-00A0B0.svg)](https://bio.tools/bio-firewall)
![Status](https://img.shields.io/badge/status-reference%20implementation-blue.svg)

> **Scope and maturity.** BioFirewall is a defensive, computational reference implementation evaluated on safe
> proxy molecules only. It contains no hazard sequences and no evasion instructions. It is a safeguard, not a
> guarantee: screening reduces risk, it does not eliminate it. It is not a substitute for institutional
> biosafety review or synthesis-stage screening.

---

## Why it exists

AI can now design DNA, including genome-writing enzymes and the cassettes they install. Biosafety controls
exist at two points, with a gap between them:

| Layer | Where it acts | Who builds it | What it misses |
|---|---|---|---|
| A. Model | the chatbot | Anthropic ASL-3, OpenAI Preparedness, DeepMind FSF | general CBRN refusal; not artifact-aware |
| B. Design and planning | the agent's genome-writing workflow | *(the gap)* | **the layer BioFirewall fills** |
| C. Synthesis | the physical DNA order | IBBIS Common Mechanism, SecureDNA | homology-based, demonstrably evadable |

An offense benchmark (ABC-Bench, NeurIPS 2025 BioSafe GenAI workshop; arXiv:2606.11150) showed that frontier
agents already produce assemblable DNA that evades the synthesis screen at Layer C. The design stage must
therefore read the artifact in-workflow, at a point where the agent cannot route around it. BioFirewall is an
automated, in-workflow screen for the hazards that are native to genome writing, namely where you edit, how,
whether the edit is heritable, and at what scale. A sequence or protein screener structurally cannot see any
of them.

## What it screens: five axes, one stratified verdict

When a design AI hands BioFirewall a genome-writing plan, the screen asks five questions and combines the
answers into a single stratified verdict. Stratification matters because almost every dangerous edit is also
legitimate research.

| Axis | Question | Examples it flags |
|---|---|---|
| 1. Cargo | What are you inserting? | a toxin or virulence factor, a low-identity AI homolog of one, a gene drive |
| 2. Locus | Where are you inserting it? | next to a cancer gene, inside a tumour suppressor, an essential or dosage-sensitive gene |
| 3. Edit type | What kind of edit? | a rearrangement creating a known oncogenic fusion, a large deletion, multiplex translocation |
| 4. Germline | Will it be inherited? | editing human embryos, eggs, or sperm (heritable, clinical) |
| 5. Scale | How big? | megabase restructuring, high-multiplex edits |

**Verdict logic.** An unambiguous match (select-agent cargo, human heritable clinical edit, a known oncogenic
fusion) returns `refuse`. Locus, edit and scale signals return `flag_for_review` with the evidence attached,
routed to a human. A clean plan returns `allow` with a signed passport. Every verdict carries a confidence
level, abstains rather than guesses when the gene or signature falls outside the knowledge base, and resists
reframing because it judges the artifact rather than the accompanying prose.

## Quickstart

```bash
pip install -e .          # requires pen-stack>=0.1.0,<0.2.0 (resolved from PyPI)
```

Or run the published container. The image is self-contained: the screen, the signed hazard knowledge base and
the vendored open data all ship inside it, so the demo and the committed-data reproduction run with no
external data and no network.

```bash
docker pull ghcr.io/ahmedanees-m/bio-firewall:0.1.0
docker run --rm ghcr.io/ahmedanees-m/bio-firewall:0.1.0                # runs examples/demo.py
docker run --rm ghcr.io/ahmedanees-m/bio-firewall:0.1.0 make reproduce # headline numbers + full test suite
```

To build it yourself instead:

```bash
docker build -t biofirewall .            # or: make docker-build
docker run --rm biofirewall              # runs examples/demo.py
```

```python
from bio_firewall import screen

# benign somatic therapeutic -> allow
screen({"intent": "insert a Factor IX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"})["decision"]
# "allow"

# human heritable clinical edit -> refuse (the germline axis)
screen({"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}})["decision"]
# "refuse"

# rearrangement that creates a known oncogenic fusion -> refuse (the edit-type axis)
screen({"edit": {"fusion_genes": ["BCR", "ABL1"]}})["decision"]
# "refuse"

# legitimate cancer modeling on a tumour suppressor -> flagged for review, not blocked
screen({"intent": "cancer modeling: disrupt a tumor suppressor", "gene": "TP53"})["decision"]
# "flag_for_review"
```

Run the demo, the benchmark, and the in-workflow agent trace:

```bash
python examples/demo.py
python -c "from bio_firewall.eval import run; print(run()['by_axis'])"
python examples/agent_integration.py        # a design-agent loop gated by the firewall
make reproduce                              # committed-data headline numbers + the test suite
```

## Architecture

BioFirewall imports `pen-stack` for reusable machinery (the biosecurity Guardian, the rules pattern,
calibration) and governs any design tool through a tool-agnostic artifact contract. It vendors open data only.

```
        design AI  (PEN-STACK / Biomni / CRISPR-GPT / raw)
                        |   genome-writing plan (artifact)
                        v
   +---------------------------------------------------------------+
   |  P1  governance spine  (screen)        framing-stripped        |
   |   |                                                            |
   |   +- P2  five-axis hazard screen                               |
   |   |       cargo | locus | edit-type | germline | scale         |
   |   |       -> combine_mono (monotone, interaction-aware)        |
   |   +- P8  calibration   (conformal confidence + abstention)     |
   |   +- graded taxonomy   (allow | partial | flag | refuse)       |
   |   +- P3  rule-governance (legality as cited data)              |
   |   +- P4  design passport (HMAC-signed, tamper-evident)         |
   |   +- P7  audit log       (hash-chained)                        |
   |   +- P9  managed access  (tier by verdict x user legitimacy)   |
   +---------------------------------------------------------------+
                        |   {decision, grade, axes, evidence, passport, access}
                        v
   in-workflow gate:  allow -> synthesis   |   flag_for_review -> human   |   refuse -> stop
   (synthesize() is hard-gated on a verifiable allow passport; P9 gates how a verdict RESOLVES per user legitimacy)
```

**The nine planes.** P1 governance spine, P2 five-axis screen, P3 rule-governance, P4 design passport,
P5 refusal and escalation, P6 red-team, P7 audit, P8 calibration, P9 managed access. With built-in screening
(P2), signed metadata (P4) and managed access (P9), BioFirewall implements the complete set of design-stage
guardrails the NTI biodesign-tool framework recommends.

**Data sources, open only.** CancerMine (CC0; oncogene, tumour suppressor, driver), DepMap (essential genes),
gnomAD (pLI and LOEUF dosage), GENCODE (coordinates), Pfam, and public control lists. A continuous-integration
test fails the build if a restricted source appears in the committed data. See
[DATA_LICENSES.md](DATA_LICENSES.md).

## Results

Each benchmark is pre-registered in `prereg/ws_biofirewall.yaml`; full method and interpretation are in
[docs/BENCHMARK.md](docs/BENCHMARK.md). Hazard is labeled by independent oracles the firewall does not use
(12 clinical insertional-oncogenesis genes plus the COSMIC Cancer Gene Census v104), so a high score reflects
generalization rather than recognition of the firewall's own gene list. Baselines are earned: B0 runs the real
Guardian signature screen; B1 is a frontier language model (`claude-opus-4-8`) acting as a blind safety
reviewer.

| Benchmark | Firewall | B0 homology | B1 frontier LLM |
|---|:--:|:--:|:--:|
| Tier-1 clinical-CIS gold (mandatory) | 100% (12/12) | 0% | 100% |
| structural-hazard interception (n=771) | 80.4% (CI .78-.83) | 0% | 77.3% (1) |
| false-refuse on legitimate research | 0% | - | 40% (refused TP53, APC) |
| red-team flip refuse->allow (46 attacks) | 0% | - | - |
| cargo ML gate, TPR@1%FPR, <=40%-id clusters | 0.72 (CI .43-.89) | 0.207 | - |

(1) B1 is measured on a pre-registered stratified sample. The homology floor catches 0% of structural-locus
hazards, which is the design-stage gap in one number. A frontier language model is a strong locus-recall
baseline, but it over-refuses legitimate research and is neither deterministic nor auditable. The firewall's
contribution on the locus axis is deterministic, flag-not-block, auditable governance, not higher raw recall.

### Can a language model be the safety check?

Four experiments compare the firewall against a frontier model and three open models that users self-host,
each given its best configuration. Two of the four dimensions separate the firewall from the language models
and two do not. Full detail: [docs/HEADTOHEAD.md](docs/HEADTOHEAD.md) and [docs/PANEL.md](docs/PANEL.md).

| Dimension | DeepSeek-v4 | Llama-4-Mav | qwen3-next | Firewall |
|---|:--:|:--:|:--:|:--:|
| D: prompt-injection flip refuse->allow | unparseable | 0.50 / 0.83 | 0.83 / 0.50 | 0% |
| B: determinism (temp-0 unstable, /10) | 0/10 | 0/10 | 0/10 | 0 |
| A: fabrication | 0% | 0% | 0% | 0% |

| C: cargo screen, sequence only | TPR [95% CI] | FPR | Refused to engage |
|---|:--:|:--:|:--:|
| Claude Haiku 4.5 | 0.01 [0, .03] | 0.01 | 0 |
| Qwen3-next-80b | 0.02 [0, .05] | 0.00 | 0 |
| Claude Sonnet 5 | 0.05 [0, .12] | 0.00 | 47% |
| Claude Opus 4.8 | 0.38 [.21, .55] | 0.00 | 45% |
| DeepSeek-v4-flash | 0.78 [.68, .88] | 0.18 | 0 |
| **ESM-2 classifier** | **0.72 @ 1% FPR** | - | - |

Per-model counts, rates and bootstrap confidence intervals are committed in `results/nvidia_headtohead/`.

- **No tested language model screens a cargo sequence.** None reaches the ESM classifier's 0.72 at 1% FPR:
  three allow almost every toxin (TPR 0.01 to 0.05), one flags most but at a prohibitive 18% false-positive
  rate, and the two frontier models decline 45 to 47% of sequences outright. These behaviours are uncalibrated
  and unstable across model revisions. This is the role the cargo ML gate fills.
- **Open language-model judges are jailbroken.** A prompt-injection string in a plan's free text flips
  refuse to allow 50 to 83% of the time. The firewall reads coordinates, not prose, and is immune by
  construction (0%).
- At the reported sample sizes the tested models are neither unstable (B) nor fabricating (A). The firewall's
  case therefore rests on C, D, and operational properties (grounded, auditable, zero per-call cost), not on
  determinism alone.

A frontier language model is a capable advisor. A language model used as the safety judge is jailbroken on
self-hosted models and unable to screen sequence cargo. The firewall is the deterministic, artifact-reading
control that makes the advisor safe to operate.

### What the screen guarantees

- **Certified false-refuse ceiling.** A distribution-free guarantee no language model offers: 0 of 288
  legitimate-research plans refused, a certified upper bound of 0.0103 on P(refuse | legitimate research),
  passing alpha in {.01, .05, .10}. Confidence is competence-conditioned and monotone (high 1.00 > moderate
  0.69 > low 0.10), with out-of-knowledge-base allows routed to low confidence, 9 of 10 of which are genuine
  misses.
- **Provably monotone combination.** Evidence is combined by a noisy-OR rule that is monotone (verified on a
  5,000-case perturbation suite), interaction-aware (co-occurring moderate signals escalate, where a maximum
  is flat), and hard-rule-exact.
- **Cross-call decomposition defence.** A per-artifact screen is defeated if a hazard is split across N calls
  that each pass. The `SessionMonitor` screens the cross-call aggregate (assembly and junction inference,
  cumulative scale, coordinated loci). On two genuine decomposition evasions, a megabase restructuring split
  into sub-50 kb deletions and a cargo split into Gibson and Type-IIS fragments, the per-artifact screen is
  blind while the session catches 100% (CI [1.0, 1.0]) at 0% false-positive.

### Screening on mechanism rather than lookup

Each novel axis screens on mechanism rather than a catalogue, so it can catch what is not yet listed.

- **De-novo fusion detection.** A mechanism screen (fusion-kinase family, oncogene roles, IG/TCR
  juxtaposition) generalizes beyond the 14-pair lookup: 90.9% recall on 471 off-list COSMIC fusion pairs,
  100% on the 112 kinase pairs, at 0% benign false-positive.
- **Positional locus.** Flags promoter- and enhancer-proximal insertions near an oncogene transcription start
  site, the SCID-X1 and LMO2 mechanism a gene-body lookup misses. 10,834 of 17,158 positional flags on real
  integration-site data fall outside an oncogene body.
- **Cargo signal is function-driven at the ranking level.** A composition-invariant representation
  (gradient-reversal DANN) retains AUROC 0.985 and TPR@5%FPR 0.967 against the composition probe's 0.930 and
  0.768 (paired AUROC +0.054, CI 0.025 to 0.099, excluding zero).

### Outcome validation of the locus axis

The locus axis is outcome-validated against in vivo insertional-oncogenesis drivers from mouse transposon
forward-genetic screens (CCGD, the Candidate Cancer Gene Database; Abbott et al., 2015).

- **Non-circular enrichment.** Because the axis already encodes curated oncogene and tumour-suppressor roles,
  the load-bearing test is the held-out subset of CCGD drivers absent from the axis's curated source, for
  which the axis can only fire through dosage sensitivity, essentiality, or the clinical common
  insertion-site list. On that subset the locus risk is significantly enriched for outcome-defined drivers:
  AUROC 0.605 (95% CI 0.596 to 0.614), odds ratio 3.34 (95% CI 3.07 to 3.65) on recurrent drivers appearing
  in two or more screens, with the enrichment carried by gnomAD dosage sensitivity (1,068) and DepMap
  essentiality (450) rather than the curated list (0). The operational full-knowledge enrichment is
  comparable at AUROC 0.618. The effect is modest, a significant enrichment rather than a strong classifier,
  which is what a mechanism-grounded flag that routes risk to review should be.
- **It reconciles the open-catalogue null.** The same axis is anti-predictive on the open human integration
  -site catalogue VISDB (AUROC 0.449), which is the wrong biology (approximately 96% HTLV, driven by viral
  oncoproteins rather than insertion-site proximity), and enriched on the right one. Same axis, opposite
  verdict, explained by biology.
- **What remains.** The validation is gene-level and in mouse, the standard preclinical genotoxicity model
  but not human. The event-level positional score awaits coordinate-level integration data with clonal-outcome
  annotation. Human clinical clonal-outcome validation and wet-lab confirmation are the higher evidential
  rungs.

The validation is pre-registered ([prereg/ws_locus_mouse_outcome.yaml](prereg/ws_locus_mouse_outcome.yaml)),
the CCGD-derived positive sets and the results are committed
([data/locus_outcome_inputs/](data/locus_outcome_inputs),
[results/locus_mouse_outcome.json](results/locus_mouse_outcome.json)), and it reproduces deterministically
with `python locus_mouse_outcome_validation.py --positives data/locus_outcome_inputs/ccgd_recurrent.txt`.

### Reported negative results

Three pre-registered strengtheners did not meet their criteria. They ship as reported negatives rather than
as claims, and the simpler method is retained in each case.

- **Neyman-Pearson conformal selection.** The likelihood-ratio selector controls the false-escalation rate at
  the target alpha (0.05 to 0.017, 0.10 to 0.064), which the discrete scalar threshold cannot do. At matched
  alpha, however, its power gap is negative and tightly estimated (-0.040, CI -0.067 to -0.015 at alpha 0.20),
  so the pre-registered criterion of strictly higher catch is not met. NP provides calibrated control rather
  than added power; the certified false-refuse bound is the operational result.
- **Confidence-gated structural fusion.** Gating the fold channel on mean pLDDT does not lift the 1%-FPR
  operating point (gated TPR@1%FPR 0.21 against ESM-alone 0.72). The cached structures are high-confidence
  (mean pLDDT 84.6; 706 of 706 test structures at or above 70), so gating fuses almost everywhere and the
  limit is fold distance on the <=40%-identity split, which gating cannot address. The structure channel
  remains a ranking-level corroborator (composition-free AUROC 0.882).
- **Cargo operating point.** Toxin and benign composition are genuinely separable, and the strict 1%-FPR gate
  is underpowered (362 held-out negatives give intervals spanning roughly 0 to 0.9). The cargo advantage is
  therefore not claimed at the strict operating point; the ranking-level result above is what the work rests
  on.

### Managed access, graded response, and standards alignment

- **Managed access plane (P9).** A tiered-access plane assigns an access tier from verdict severity and a
  verified user-legitimacy level, and gates how the verdict resolves: a `refuse` is never unlocked at any
  tier; a `flag_for_review` releases under review for a verified user and is held for an unverified one; an
  out-of-knowledge-base allow escalates one notch. The credentialing authority is a documented integration
  point, not an operational claim.
- **Graded-refusal taxonomy.** The stratified verdict is formalized into allow, partial, flag_for_review and
  refuse, mapped deterministically and totally from the per-axis findings. A single low-severity
  research-context mechanism flag becomes `partial` (general context, no actionable detail), while a
  scope-level flag, a sensitive axis, or co-occurring flags route to full review. A deterministic content gate
  verifies that a `partial` response carries no sequences, coordinates, oligos, protocol steps or restriction
  sites; a leaky partial collapses to review. Grounded in the partial-compliance finding (Zheng et al.,
  EMNLP 2025).
- **Standards alignment.** The safe-proxy benchmark exports in a shape compatible with NIST baseline
  screening (blinded record ids plus a separate answer key, a declared schema, a content checksum), validated
  by a continuous-integration test. The knowledge base documents its alignment to the IBBIS DNA Screening
  Standards Consortium with explicit hooks where the standard is still forming, and makes no conformance
  claim. See [docs/STANDARDS.md](docs/STANDARDS.md).

### Reproducibility and disclosure

- **System card** ([docs/SYSTEM_CARD.md](docs/SYSTEM_CARD.md)): what a green `allow` does and does not
  guarantee, nine enumerated failure modes, and a scope and limit statement for every headline claim.
- **One-command reproduction.** `make reproduce` regenerates the committed-data headline numbers and runs the
  full test suite that validates every metric path; `make reproduce-local` regenerates the data-dependent
  benchmarks. Data releases are pinned, and `.zenodo.json` and `CITATION.cff` carry the deposit metadata. See
  [REPRODUCTION.md](REPRODUCTION.md).
- **Living, signed hazard knowledge base** ([docs/HAZARD_KB.md](docs/HAZARD_KB.md)): 114 versioned,
  provenanced, HMAC-signed signatures, with a consistency gate that prevents the knowledge base drifting from
  what the screen uses.
- **Recorded in-workflow trace** ([examples/agent_integration.py](examples/agent_integration.py)): a design
  agent run through the gate. Four of six plans are intercepted mid-workflow, including a reframed oncogenic
  fusion with benign prose and a hazardous artifact, refused on its artifact; two benign plans reach
  synthesis; the audit chain stays intact. `synthesize()` is hard-gated on a verifiable allow passport.
- **Fair, pre-registered panel** ([docs/PANEL.md](docs/PANEL.md)): the control-versus-advisor comparison as a
  reusable artifact with a fixed prompt, rubric and offline replay, the language model given its best
  configuration, and an explicit on-prem-versus-API axis.

## Repository layout

```
bio-firewall/
|-- bio_firewall/
|   |-- intercept/spine.py            P1 governance spine: the public screen() entry point
|   |-- intercept/session.py          cross-call session aggregator (assembly / scale / coordinated loci)
|   |-- integrate/agent_gate.py       in-workflow gate; synthesize() hard-gated on an allow passport
|   |-- access/managed.py             P9 managed access: tier by verdict x user legitimacy; screen_managed()
|   |-- respond/graded.py             allow / partial / flag / refuse taxonomy + partial content gate
|   |-- standards/                    nist_export.py (NIST-compatible export) + ibbis.py (DSSC + OSTP)
|   |-- hazard/                       P2 the five-axis screen
|   |   |-- cargo.py, cargo_ml.py        axis 1: Guardian signatures + function-aware ESM2 classifier
|   |   |-- locus.py, locus_pos.py       axis 2: oncogene / TSG / essential / dosage; positional (promoter, enhancer)
|   |   |-- edit_type.py, edit_mech.py   axis 3: curated fusions; de-novo oncogenic fusion by mechanism
|   |   |-- germline.py                  axis 4: heritability / germline accessibility
|   |   |-- scale.py                     axis 5: megabase / high-multiplex amplifier
|   |   |-- struct_channel.py            structural (fold) channel + 3-signal ensemble (abstain on disagreement)
|   |   |-- combine.py, combine_mono.py  provably monotone, interaction-aware evidence combiner
|   |   |-- finding.py                   the per-axis Finding contract
|   |-- calibrate/                    P8 confidence: confidence.py (tiers + abstention);
|   |   |                                 conformal.py (competence-conditioned confidence + false-refuse certificate)
|   |   |                                 conformal_np.py (Neyman-Pearson likelihood-ratio conformal selection)
|   |-- adapters/                     tool-agnostic artifact contract + two reference integrations
|   |   |-- pen_stack_adapter.py         govern a PEN-STACK design plan
|   |   |-- crispr_gpt_adapter.py        govern a CRISPR-GPT-shaped plan (the contract is not PEN-STACK-specific)
|   |   |-- generic_artifact.py          the neutral artifact contract any planner can target
|   |   |-- cloudlab_gate.py             gate the PEN-STACK cloud-lab bridge on a verified allow passport
|   |   |-- writespec.py                 screen the typed PEN-STACK WriteRequest (SBOL3) directly
|   |   |-- reconcile.py                 conservative-meet reconcile with pen-stack's in-design safety_gate
|   |-- passport/, audit/             P4 signed design passport; P7 hash-chained audit log
|   |-- kb/registry.py                versioned, signed hazard knowledge-base loader
|   |-- data.py                       open-data loaders (CancerMine / DepMap / gnomAD / fusions / oncogene TSS)
|   |-- vendored_data/                open (CC0 / CC-BY) hazard data as parquet / yaml / npz;
|   |                                 hazard_kb/ signed KB releases; cargo_centroids.npz frozen ESM2 centroids
|   |-- eval/                         the benchmark suites (the empirical evidence)
|       |-- bench.py, redteam.py         the safe-proxy per-axis benchmark + the P6 reframing red-team
|       |                                (re-exported as bio_firewall.eval.run / reframing_resistance / ...)
|       |-- hazard_bench/                de-circularized interception, red-team, calibration
|       |   |-- run_all.py, report.py         the benchmark driver + run persistence (JSON + report)
|       |   |-- oracles.py, multi_oracle.py   independent labels: Tier-1 clinical-CIS, COSMIC CGC, OncoKB (local-only)
|       |   |-- generate.py, baselines.py, score.py    proxies, earned baselines, metrics + bootstrap CIs
|       |   |-- redteam.py                    single-call red-team (evasion families, flip rate refuse->allow)
|       |   |-- calibrate_bench.py            tier validity, risk-coverage, abstention utility
|       |   |-- conformal_bench.py            false-refuse certificate + monotone confidence
|       |   |-- decomp_redteam.py             cross-call decomposition red-team
|       |   |-- locus_outcome.py              locus outcome floor on the open integration-site catalogue
|       |   |-- edit_mech_bench.py            de-novo fusion generalization
|       |   |-- locus_pos_bench.py            positional locus coverage
|       |   |-- conformal_np_bench.py         NP-conformal versus scalar head-to-head
|       |   |-- nvidia_headtohead.py          the control-versus-advisor panel
|       |-- cargo_bench/                 run.py (cargo gate), decorr.py (composition decorrelation),
|       |                                struct_bench.py, struct_gated_bench.py (structural channel)
|       |-- headtohead/                  fabrication, paraphrase and jailbreak experiments
|-- locus_mouse_outcome_validation.py CCGD outcome-validation runner (non-circular)
|-- data/locus_outcome_inputs/        CCGD-derived human-ortholog driver lists (ccgd_recurrent.txt,
|                                     ccgd_all.txt) + SOURCE.txt
|-- results/                          frozen results:
|   |-- locus_mouse_outcome.json         recurrent-driver positives (held-out AUROC 0.605, OR 3.34)
|   |-- locus_mouse_outcome_all.json     all-driver positives (held-out AUROC 0.576, OR 2.76)
|   |-- locus_outcome_visdb.json         the open-catalogue result, gate not met (AUROC 0.449, OR 0.58)
|   |-- nvidia_headtohead/               control-versus-advisor panel (summary + per-model JSON)
|-- standards/nist_benchmark_export.json   NIST-compatible benchmark export (blinded ids + answer key)
|-- docs/                             THREAT_MODEL, HAZARD_TAXONOMY, BENCHMARK, HEADTOHEAD, SYSTEM_CARD,
|                                     PANEL, HAZARD_KB, STANDARDS, integration_cloudlab
|-- examples/                         demo.py; agent_integration.py + agent_trace.json (the recorded trace)
|-- tools/                            build_hazard_kb.py (regenerate the signed KB);
|                                     export_nist_benchmark.py (regenerate the NIST export)
|-- prereg/                           ws_biofirewall.yaml, ws_locus_mouse_outcome.yaml, ws_cloudlab_gate.yaml,
|                                     ws_writespec.yaml, ws_verify_reconcile.yaml
|-- tests/                            167 tests, including the data-license gate, the Tier-1 100%-catch
|                                     regression gate, and 22 adversarial cargo-screen regression tests
|                                     (2 are environment-gated skips: the local-only oracle and a
|                                     pen-stack-checkout end-to-end test)
|-- Makefile, REPRODUCTION.md         one-command reproduction + the clean-image protocol
|-- Dockerfile, .dockerignore         pinned-Python reproduction image (build-time smoke test)
|-- .gitignore                        the local-only data policy (restricted oracles and run artifacts
|                                     excluded; the open result files re-included)
|-- .github/workflows/                ci.yml (lint + the full suite against the pinned pen-stack);
|                                     release-image.yml (publishes the verified image to ghcr.io)
|-- CITATION.cff, .zenodo.json        citation and Zenodo deposit metadata
|-- pyproject.toml, LICENSE, DATA_LICENSES.md
```

> **Benchmark data is local-only by design.** The code (loaders, generators, harnesses) is committed; the
> license-restricted oracles (COSMIC, OncoKB), the cargo sequences, the frontier-model verdicts and the run
> artifacts live outside the repository and are never committed. The repository ships the method and the
> aggregate results.

## Limitations

- The locus axis routes elevated risk to human review and does not output a cancer probability; it flags on
  mechanism rather than emitting a calibrated rate. It is outcome-validated against mouse in vivo
  insertional-oncogenesis drivers (non-circular held-out AUROC 0.605, odds ratio 3.34), but the effect is
  modest and three rungs remain: the validation is gene-level, it is in mouse rather than human, and human
  clinical clonal-outcome validation (controlled-access dbGaP and EGA) and wet-lab confirmation are deferred.
  The open human catalogue (VISDB) is not predictive (AUROC 0.449) because it is the wrong, HTLV-driven
  biology.
- The function-aware cargo ML is not novel at the component level (compare ToxDL, Pan et al. 2020; OmniTox
  and function-aware screening, Mathew et al. 2025, PMC12699701). The contribution is the integrated
  five-axis governed system plus the benchmark and red-team, with the locus, edit, germline and scale axes as
  the new capability. The cargo signal is substantially non-compositional in ranking, but its advantage over
  a composition baseline at the strict 1%-FPR operating point is not statistically established on the
  held-out set, so the work does not lead on the cargo gate.
- The conformal false-refuse ceiling bounds over-refusal, not hazard-catch. It certifies
  P(refuse | legitimate research) <= alpha; it does not prove all hazards are caught. The
  competence-conditioned confidence flags the knowledge-base boundary but does not eliminate the underlying
  coverage gap.
- Safe proxies bound every cargo claim, which is a methodological necessity. Wet-lab validation is future
  work. The benchmark measures concordance with an independent hazard model and lift over real baselines,
  which is necessary but not sufficient for real-world safety.
- The decomposition aggregator is necessary, not sufficient. It catches the assembly, scale and
  coordinated-loci decompositions it models; a novel cross-call obfuscation can still evade it, which is a
  named and reported residual.
- Managed access (P9) is a mechanism, not a deployed authority. The plane enforces tiers and verifies through
  pluggable hooks; the credentialing authority is an integration point the deployment supplies. Standards
  alignment tracks a moving target (the IBBIS DSSC standards are still forming and the 2024 OSTP framework
  may be revised), so the artifact ships alignment intent plus schema hooks and makes no conformance claim.
- The control-versus-advisor results are specific to the model versions tested (`claude-opus-4-8`,
  `claude-sonnet-5`, `claude-haiku-4-5`, `deepseek-v4-flash`, `qwen3-next-80b`, `llama-4-maverick`). Model
  endpoints are mutable, and a stronger or differently tuned model could shift the A, B and D results.
- The system has been validated computationally by a single group and has not been deployed in production or
  adopted elsewhere. Independent reproduction extends to the committed open artifact.

## Responsible use

Defensive screen, safe proxies only, no evasion cookbook, and the artifact decides rather than the framing.
Signatures are at the function, family and taxon level (public Pfam and control-list references); no hazard
sequences are shipped or required. BioFirewall is not a substitute for institutional biosafety review, IBC
approval, or synthesis-stage screening. It is an additional, auditable layer that makes a capable design AI
safer to operate.

## License and attribution

Apache-2.0. Built on [PEN-STACK](https://github.com/ahmedanees-m/pen-stack) (open infrastructure for genome
writing). Developed at Vellore Institute of Technology, Vellore. Authors and ORCIDs are listed in
[CITATION.cff](CITATION.cff).
