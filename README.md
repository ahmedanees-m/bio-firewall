# BioFirewall

**A rule-governed, genome-writing-native biosecurity middleware that supervises agentic design AI.**

BioFirewall sits between a DNA-design AI and the DNA synthesizer. It inspects the *plan* the AI produced, not only
the final sequence, and returns one of **`allow`**, **`flag_for_review`**, or **`refuse`**, with cited evidence and a
signed design passport. It is the missing design-stage guardrail: a firewall for genome writing.

[![CI](https://github.com/ahmedanees-m/bio-firewall/actions/workflows/ci.yml/badge.svg)](https://github.com/ahmedanees-m/bio-firewall/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-113%20passing-success.svg)
![Version](https://img.shields.io/badge/version-0.9.0-blue.svg)
![Status](https://img.shields.io/badge/status-alpha%20reference-orange.svg)

> **Scope and maturity.** BioFirewall is a defensive, early-stage, computational reference implementation evaluated on
> safe proxy molecules only. It contains no hazard sequences and no evasion instructions. It is a safeguard, not a
> guarantee: screening reduces risk, it does not eliminate it. It is not a substitute for institutional biosafety
> review or synthesis-stage screening.

---

## Why it exists

AI can now design DNA, including genome-writing enzymes and the cassettes they install. Biosafety controls exist at
two points, with a gap between them:

| Layer | Where | Who builds it | Gap |
|---|---|---|---|
| A. Model | the chatbot | Anthropic ASL-3, OpenAI Preparedness, DeepMind FSF | general CBRN; not artifact-aware |
| B. Design / planning | the agent's genome-writing workflow | (empty) | the layer BioFirewall fills |
| C. Synthesis | the physical DNA order | IBBIS Common Mechanism, SecureDNA | homology-based, demonstrably evadable |

A 2026 offense benchmark (ABC-Bench, NeurIPS 2025 BioSafe GenAI workshop; arXiv:2606.11150) showed that frontier
agents already produce assemblable DNA that evades the synthesis screen at Layer C. The design stage (Layer B) must
therefore read the artifact
in-workflow, where the agent cannot route around it. BioFirewall is the first automated, in-workflow screen for the
genome-writing-native hazards (where you edit, how, whether it is heritable, and at what scale), dimensions that a
sequence or protein screener structurally cannot see.

## What it does: the five-axis screen

When a design AI hands BioFirewall a genome-writing plan, the screen asks five questions and combines the answers
into one stratified verdict (stratified because almost every dangerous edit is also legitimate research):

| Axis | Question | Examples it flags |
|---|---|---|
| 1. Cargo | What are you inserting? | a toxin or virulence factor, a low-identity AI homolog of one, a gene drive |
| 2. Locus (the edge) | Where are you inserting it? | next to a cancer gene, inside a tumour suppressor, an essential or dosage-sensitive gene |
| 3. Edit-type | What kind of edit? | a rearrangement that creates a known oncogenic fusion, a large deletion, multiplex translocation |
| 4. Germline | Will it be inherited? | editing human embryos, eggs, or sperm (heritable, clinical) |
| 5. Scale | How big? | megabase restructuring, high-multiplex edits |

**Verdict logic (stratification, not a blocklist).** An unambiguous match (select-agent cargo, human heritable
clinical edit, a known oncogenic fusion) returns `refuse`. The locus, edit, and scale signals return
`flag_for_review` with the evidence, routed to a human. A clean plan returns `allow` with a signed passport. The
verdict carries a confidence level, abstains rather than guess, and resists reframing (it judges the artifact, not
the cover story).

## Quickstart

```bash
pip install -e .          # requires pen-stack>=6.6.0
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
make reproduce                              # regenerate the committed-data headline numbers + run the test suite
```

## Architecture

BioFirewall imports `pen-stack` for reusable machinery (the biosecurity Guardian, the rules pattern, calibration) and
governs any design tool through a tool-agnostic artifact contract. It vendors open data only.

```
        design AI  (PEN-STACK / Biomni / CRISPR-GPT / raw)
                        |   genome-writing plan (artifact)
                        v
   +---------------------------------------------------------------+
   |  P1  governance spine  (screen)        framing-stripped       |
   |   |                                                           |
   |   +- P2  five-axis hazard screen                              |
   |   |       cargo | locus | edit-type | germline | scale        |
   |   |       -> combine_mono (monotone, interaction-aware)       |
   |   +- P8  calibration   (conformal confidence + abstention)    |
   |   +- graded taxonomy   (allow | partial | flag | refuse)      |
   |   +- P3  rule-governance (legality as cited data)             |
   |   +- P4  design passport (HMAC-signed, tamper-evident)        |
   |   +- P7  audit log       (hash-chained)                       |
   |   +- P9  managed access  (tier by verdict x user legitimacy)  |
   +---------------------------------------------------------------+
                        |   {decision, grade, axes, evidence, passport, access}
                        v
   in-workflow gate:  allow -> synthesis   |   flag_for_review -> human   |   refuse -> stop
   (synthesize() is hard-gated on a verifiable allow passport; P9 gates how a verdict RESOLVES per user legitimacy)
```

**The nine planes.** P1 governance spine, P2 five-axis screen, P3 rule-governance, P4 design passport, P5 refusal
and escalation, P6 red-team, P7 audit, P8 calibration, and (v0.8) P9 managed access. With built-in screening (P2),
signed metadata (P4), and managed access (P9), BioFirewall implements the complete set of design-stage guardrails the
NTI biodesign-tool framework recommends.

**Data sources, open only (a CI test fails the build if a restricted source appears).** CancerMine (CC0;
oncogene / TSG / driver), DepMap (essential genes), gnomAD (pLI / LOEUF dosage), GENCODE (coordinates), Pfam, and
public control lists. See [DATA_LICENSES.md](DATA_LICENSES.md).

## Repository layout

```
bio-firewall/
|-- bio_firewall/
|   |-- intercept/spine.py            P1 governance spine: the public screen() entry point
|   |-- intercept/session.py          v0.5 WS-DECOMP: cross-call session aggregator (assembly / scale / coordinated-loci)
|   |-- integrate/agent_gate.py       v0.7 WS-INTEGRATE: in-workflow gate; synthesize() hard-gated on an allow passport
|   |-- access/managed.py             v0.8 P9 WS-MANAGED: tiered access by verdict x user legitimacy; screen_managed()
|   |-- respond/graded.py             v0.8 WS-GRADED: allow/partial/flag/refuse taxonomy + partial content gate
|   |-- standards/                    v0.8 WS-STANDARDS: nist_export.py (NIST-compatible benchmark) + ibbis.py (DSSC + OSTP)
|   |-- hazard/                       P2 the five-axis screen
|   |   |-- cargo.py, cargo_ml.py        axis 1: Guardian signatures + function-aware ESM2 classifier
|   |   |-- locus.py, locus_pos.py       axis 2: oncogene / TSG / essential / dosage; v0.6 positional (promoter/enhancer)
|   |   |-- edit_type.py, edit_mech.py   axis 3: curated fusions; v0.6 de-novo oncogenic-fusion-by-mechanism
|   |   |-- germline.py                   axis 4: heritability / germline-accessibility
|   |   |-- scale.py                      axis 5: megabase / high-multiplex amplifier
|   |   |-- struct_channel.py             v0.6 structural (fold) channel + 3-signal ensemble (abstain on disagreement)
|   |   |-- combine.py, combine_mono.py   v0.6 provably-monotone, interaction-aware evidence combiner
|   |   |-- finding.py                    the per-axis Finding contract
|   |-- calibrate/                    P8 confidence: confidence.py (tiers + abstention);
|   |   |                                 conformal.py (v0.4 competence-conditioned confidence + false-refuse certificate)
|   |   |                                 conformal_np.py (v0.8 Neyman-Pearson likelihood-ratio conformal selection)
|   |-- passport/, audit/             P4 signed design passport; P7 hash-chained audit log
|   |-- kb/                           v0.7 WS-LIVING-KB: versioned, signed hazard knowledge base loader
|   |-- adapters/                     tool-agnostic artifact contract + the PEN-STACK reference integration
|   |-- data.py                       open-data loaders (CancerMine / DepMap / gnomAD / fusions / oncogene TSS)
|   |-- eval/                         the benchmark suites (the empirical evidence)
|       |-- hazard_bench/             Benchmarks 1 / 3 / 4: de-circularized interception, red-team, calibration
|       |   |-- oracles.py, multi_oracle.py   independent labels: Tier-1 clinical-CIS, COSMIC CGC, OncoKB (local-only)
|       |   |-- generate.py, baselines.py, score.py    proxies, earned B0/B1 baselines, metrics + bootstrap CIs
|       |   |-- conformal_bench.py            B4b: false-refuse certificate + monotone confidence (v0.4)
|       |   |-- decomp_redteam.py             B5: decomposition red-team (v0.5)
|       |   |-- locus_outcome.py              B6: locus outcome floor on VISDB (v0.5)
|       |   |-- edit_mech_bench.py            B8: de-novo fusion generalization (v0.6)
|       |   |-- locus_pos_bench.py            B9: positional locus coverage (v0.6)
|       |   |-- conformal_np_bench.py         v0.8: NP-conformal vs v0.4 scalar head-to-head (documented null)
|       |   |-- nvidia_headtohead.py          the control-vs-advisor panel (A/B/C/D via NVIDIA NIM)
|       |-- cargo_bench/run.py, decorr.py, struct_bench.py, struct_gated_bench.py   B2 gate; B2b; B10; v0.8 gated struct
|       |-- headtohead/              the v1.1 control-vs-advisor experiments (fabrication / paraphrase / jailbreak)
|-- locus_mouse_outcome_validation.py   v0.9 WS-LOCUS-MOUSE-OUTCOME: CCGD outcome-validation runner (non-circular)
|-- vendored_data/                   open (CC0 / CC-BY) hazard data as parquet / yaml; hazard_kb/ signed KB releases
|-- data/locus_outcome_inputs/       v0.9 CCGD-derived human-ortholog driver lists (ccgd_recurrent/all.txt) + SOURCE
|-- results/locus_mouse_outcome*.json   v0.9 frozen CCGD outcome-validation results (held-out AUROC 0.605, OR 3.34)
|-- standards/nist_benchmark_export.json   v0.8 NIST-compatible benchmark export (blinded ids + answer key)
|-- docs/                            THREAT_MODEL, HAZARD_TAXONOMY, BENCHMARK, HEADTOHEAD, SYSTEM_CARD, PANEL, HAZARD_KB, STANDARDS
|-- examples/                        demo.py; agent_integration.py + agent_trace.json (the recorded in-workflow trace)
|-- tools/build_hazard_kb.py, tools/export_nist_benchmark.py   regenerate the signed KB; regenerate the NIST export
|-- prereg/                          ws_biofirewall.yaml (criteria + frozen results); ws_locus_mouse_outcome.yaml (v0.9)
|-- tests/                           113 tests (incl. the data-license CI gate and the Tier-1 100%-catch regression gate)
|-- Makefile, REPRODUCTION.md        one-command reproduction + the clean-image protocol
|-- CITATION.cff, .zenodo.json       citation and Zenodo deposit metadata
|-- pyproject.toml, LICENSE, DATA_LICENSES.md
```

> **Benchmark data is local-only by design.** The code (loaders, generators, harnesses) is committed; the
> license-restricted oracles (COSMIC, OncoKB), the cargo sequences, the frontier-model verdicts, and all run artifacts
> live outside the repository (gitignored) and are never committed. The repository ships the method and the
> aggregate results.

## Results

Each benchmark is pre-registered in `prereg/ws_biofirewall.yaml`; full method and interpretation are in
[docs/BENCHMARK.md](docs/BENCHMARK.md). Hazard is labeled by independent oracles the firewall does not use (12
clinical insertional-oncogenesis genes plus the COSMIC Cancer Gene Census v104), so a high score reflects
generalization rather than recognition of the firewall's own gene list. Baselines are earned: B0 runs the real
Guardian signature screen; B1 is a frontier LLM (`claude-opus-4-8`) acting as a blind safety reviewer.

| Benchmark | Firewall | B0 homology | B1 frontier LLM |
|---|:--:|:--:|:--:|
| Tier-1 clinical-CIS gold (mandatory) | 100% (12/12) | 0% | 100% |
| structural-hazard interception (n=771) | 80.4% (CI .78-.83) | 0% | 77.3% (1) |
| false-refuse on legitimate research | 0% | - | 40% (refused TP53, APC) |
| red-team flip refuse->allow (46 attacks) | 0% | - | - |
| cargo ML gate, TPR@1%FPR, <=40%-id clusters | 0.72 (CI .43-.89) | 0.207 | - |

(1) B1 measured on a pre-registered stratified sample. The homology floor catches 0% of structural-locus hazards,
which confirms the design-stage gap. A frontier LLM is a strong locus-recall baseline but over-refuses legitimate
research and is non-deterministic and non-auditable. The firewall's contribution on the locus axis is deterministic,
flag-not-block, auditable governance, not a claim of higher raw recall.

### Control versus advisor: can an LLM be the safety check?

The same four experiments were run against Claude Opus 4.8 and three open models that users self-host
(`deepseek-v4`, `llama-4-maverick`, `qwen3-next-80b`), each given its best configuration. Powering up the experiment
withdrew two weak claims and confirmed two strong ones. Full detail: [docs/HEADTOHEAD.md](docs/HEADTOHEAD.md) and
[docs/PANEL.md](docs/PANEL.md).

| Dimension | DeepSeek-v4 | Llama-4-Mav | qwen3-next | Firewall |
|---|:--:|:--:|:--:|:--:|
| C: cargo screen, seq-only TPR / FPR (n=200) | 0.00 / 0.00 | 0.60 / 0.49 | 0.02 / 0.00 | ESM 0.72 @ 1% FPR |
| D: prompt-injection flip refuse->allow | unparseable | 0.50 / 0.83 | 0.83 / 0.50 | 0% |
| B: determinism (temp-0 unstable, /10) | 0/10 | 0/10 | 0/10 | 0 |
| A: fabrication | 0% | 0% | 0% | 0% |

- **No tested LLM can screen a cargo sequence.** Two under-screen (catch close to zero toxins), one over-flags at
  random (TPR 0.60 at a 49% false-positive rate); none approaches the function-aware classifier. This is the role of
  the cargo ML gate.
- **Open LLM judges are jailbroken.** A prompt-injection string in a plan's free text flips refuse->allow 50-83% of
  the time. The firewall reads coordinates, not prose, and is immune by construction (0%).
- At powered N the LLMs were neither unstable (B) nor fabricating (A). The firewall's case therefore rests on C, D,
  and operational properties (grounded, auditable, zero per-call cost), not on determinism.

A frontier LLM is a capable advisor. An LLM used as the safety judge is jailbroken on self-hosted models and unable
to screen sequence cargo. The firewall is the deterministic, artifact-reading control that makes the advisor safe to
operate.

### v0.4.0 - The Hardened Core

- **Cargo decorrelation (B2b).** Is the cargo signal function-driven or the amino-acid-composition shortcut?
  Toxin and benign composition are genuinely separable (the confound is real), and the strict 1%-FPR operating-point
  gate is underpowered (362 held-out negatives give CIs spanning roughly 0 to 0.9), so claim C is not led as a clean
  operating-point win. The powered adjudication is decisive at the ranking level: a composition-invariant
  representation (gradient-reversal DANN) retains AUROC 0.985 and TPR@5%FPR 0.967 versus the composition probe's
  0.930 / 0.768 (paired AUROC +0.054, CI 0.025-0.099, excludes 0). The signal is substantially non-compositional in
  ranking.
- **Conformal false-refuse ceiling (B4b).** Replaces the withdrawn determinism headline with a guarantee an LLM
  cannot offer: 0 of 288 legitimate-research plans refused, a certified upper bound of 0.0103 on
  P(refuse | legitimate research), passing alpha in {.01, .05, .10}. A competence-conditioned confidence resolves the
  v0.3 inversion: monotone high 1.00 > moderate 0.69 > low 0.10, with out-of-knowledge-base allows routed to low
  confidence (9 of 10 of which are genuine misses).

### v0.5.0 - The Validated Edge

- **Decomposition aggregator (B5).** Closes the one untested attack: a hazard split across N calls that each pass.
  The `SessionMonitor` screens the cross-call aggregate (assembly/junction inference, cumulative scale, coordinated
  loci). On the two genuine decomposition evasions (a >1 Mb restructuring split into sub-50 kb deletions, and a cargo
  split into Gibson / Type-IIS fragments), the per-artifact screen is blind (each piece passes) while the session
  catches 100% (CI [1.0, 1.0]) at 0% false-positive. The coordinated-loci signal is reported as defense-in-depth, not
  an evasion.
- **Locus outcome floor (B6), access-gated.** The enrichment harness was run on the open VISDB integration-site
  catalogue (127,234 sites). The pre-registered enrichment gate is not met (overall AUROC 0.449, OR 0.577). The
  diagnosis is informative: 96% of the open tumor-associated sites are HTLV (ATL), whose integration biology is
  viral-oncoprotein-driven rather than insertional-oncogenesis-at-oncogenes. The readily available open data is the
  wrong biology to validate a gammaretroviral model, so the locus axis ships unchanged and outcome validation remains
  pending on the deferred controlled-access clonal-outcome data.

### v0.6.0 - The Generalized Screen

Each novel axis is moved from a lookup to a mechanism, so the screen can catch what is not catalogued.

- **Monotone combiner (B7), pass.** The max-severity cascade is replaced by a noisy-OR combiner that is provably
  monotone (verified on a 5,000-case perturbation suite), interaction-aware (co-occurring moderate signals escalate,
  where a max is flat), and hard-rule-exact, with decisions identical to v0.5.
- **De-novo fusion detection (B8), pass.** A mechanism screen (fusion-kinase family, oncogene roles, IG/TCR
  juxtaposition) generalizes beyond the 14-pair lookup: 90.9% recall on 471 off-list COSMIC fusion pairs (100% on the
  112 kinase pairs) at 0% benign false-positive.
- **Positional locus (B9).** Flags promoter/enhancer-proximal insertions near an oncogene TSS, the SCID-X1/LMO2
  mechanism a gene-body lookup misses (10,834 of 17,158 positional flags on real VISDB sites are not in an oncogene
  body). The outcome-AUROC-improvement claim is deferred (access-gated).
- **Structural channel (B10), negative result at the operating point.** A composition-free fold signal (AlphaFold-DB
  plus Foldseek, no GPU) and a 3-signal ensemble that abstains on disagreement. At 1% FPR it does not add over ESM
  (the <=40%-id holdout makes held-out toxins structurally distant), but structure-alone AUROC is 0.882, and being
  composition-free it independently corroborates the v0.4 non-compositionality result at the ranking level. The
  channel and abstention are shipped; the 1%-FPR claim is reported as not met.

### v0.7.0 - The Reproducible Artifact

- **System card** ([docs/SYSTEM_CARD.md](docs/SYSTEM_CARD.md)): what a green `allow` does and does not guarantee,
  nine enumerated failure modes, and a scope and limit statement for every headline claim.
- **One-command reproduction.** `make reproduce` regenerates the committed-data headline numbers and runs the
  full test suite that validates every metric path; `make reproduce-local` regenerates the data-dependent benchmarks; data
  releases are pinned; `.zenodo.json` and `CITATION.cff` provide the deposit metadata; see
  [REPRODUCTION.md](REPRODUCTION.md).
- **Living, signed hazard KB** ([docs/HAZARD_KB.md](docs/HAZARD_KB.md)): 80 versioned, provenanced, HMAC-signed
  signatures, with a CI consistency gate that prevents the KB drifting from what the screen uses.
- **Recorded in-workflow trace** ([examples/agent_integration.py](examples/agent_integration.py)): a design agent run
  through the gate. Four of six plans are intercepted mid-workflow (including a reframed oncogenic fusion, benign
  prose and hazardous artifact, refused on its artifact), two benign plans reach synthesis, and the audit chain stays
  intact. `synthesize()` is hard-gated on a verifiable allow passport.
- **Fair, pre-registered panel** ([docs/PANEL.md](docs/PANEL.md)): the control-versus-advisor comparison as a
  reusable artifact with a fixed prompt and rubric, the LLM given its best configuration, and an explicit
  on-prem-versus-API axis. The independent re-run and the Zenodo DOI mint are flagged as external and author actions.

### v0.8.0 - The Completeness Cycle

This cycle completes the artifact against the field. All references were independently re-verified before any code
(see `DATA_ID_VERIFICATION_v0.8.md`); three corrections were carried in, including the ABC-Bench venue (NeurIPS 2025
BioSafe GenAI workshop, not ICML). Per a pre-registered publication gate, three workstreams land and two are gated
"iff they pass"; both gated experiments hit their pre-committed fallback and are reported as documented nulls.

- **Managed access plane (P9), pass.** A tiered-access plane assigns an access tier from the verdict severity and a
  verified user-legitimacy level, and gates how the verdict resolves: a `refuse` is never unlocked at any tier; a
  `flag_for_review` releases under review for a verified user and is held for an unverified one; an out-of-knowledge
  -base allow escalates one notch. The tier and the legitimacy-evidence hash are bound into the signed passport and
  the hash-chained audit, so mutating the tier breaks the signature. The credentialing authority is a documented
  integration point, not an operational claim. With P2 screening, P4 signed metadata, and P9 managed access, the
  artifact now implements the complete set of design-stage guardrails the NTI framework recommends.
- **Graded-refusal taxonomy, pass.** The stratified verdict is formalized into allow / partial / flag_for_review /
  refuse, mapped deterministically and totally from the per-axis findings: a single low-severity research-context
  mechanism flag becomes `partial` (general context, no actionable detail), while a scope-level flag, a sensitive
  axis, or co-occurring flags route to full review. A deterministic content gate verifies a `partial` response carries
  no sequences, coordinates, oligos, protocol steps, or restriction sites (negative controls confirm it has teeth);
  a leaky partial collapses to review. Grounded in the partial-compliance finding (Zheng et al., EMNLP 2025).
- **Standards alignment, pass.** The safe-proxy benchmark exports in a NIST-baseline-screening-compatible shape
  (blinded record ids plus a separate answer key, a declared schema, a content checksum), validated by a CI test. The
  living knowledge base documents its alignment to the IBBIS DNA Screening Standards Consortium with explicit hooks
  where the standard is still forming and no conformance claim. An OSTP interagency-window note frames design-stage
  governance as complementary to synthesis-stage screening. See [docs/STANDARDS.md](docs/STANDARDS.md).
- **Neyman-Pearson conformal selection, documented null.** On the firewall corpus (COSMIC v104, gene-disjoint split,
  201 test hazards) the NP likelihood-ratio selector controls the false-escalation rate at the target alpha
  (0.05 -> 0.017, 0.10 -> 0.064), which the discrete v0.4 scalar threshold cannot do (it sits at a fixed
  false-escalation of 0.18). But at matched alpha the NP power gap is negative and tightly estimated (for example,
  -0.040, CI -0.067 to -0.015 at alpha 0.20), so the pre-registered gate (strictly higher catch at matched alpha) is
  not met. NP's value is calibrated control, not more power; the v0.4 certified false-refuse bound stands as the
  operational headline and NP is a documented fast-follow.
- **Confidence-gated structural fusion, documented null with a sharper diagnosis.** Gating the fold channel on mean
  pLDDT does not lift the 1%-FPR operating point (gated TPR@1%FPR 0.21 versus ESM-alone 0.72). The reason is now
  identified: the cached structures are high-confidence (mean pLDDT 84.6; 706 of 706 test structures at or above 70),
  so gating fuses almost everywhere and the v0.6 failure is fold-distance on the <=40%-identity split, not low
  confidence, which gating cannot fix. The structure channel remains a ranking-level corroborator (composition-free
  AUROC 0.882); no operating-point lift is claimed.

### v0.9.0 - The Outcome-Validated Edge

This cycle converts the project's central standing limitation: the locus axis previously flagged on mechanism and was
not outcome-validated. The screening code is unchanged; v0.9.0 adds an outcome-validation against real in vivo
insertional-oncogenesis drivers from mouse transposon forward-genetic screens (CCGD, the Candidate Cancer Gene
Database; Abbott et al., 2015). All references were independently re-verified, and the positive sets were re-derived
from the live source and the result re-run to an exact match before integration.

- **Locus axis, outcome-validated (non-circular).** Because the axis already encodes curated oncogene and tumour
  -suppressor roles, the load-bearing test is the held-out subset of CCGD drivers absent from the axis's curated source,
  for which the axis can only fire through dosage-sensitivity, essentiality, or the clinical CIS list. On this held-out,
  non-circular subset the locus risk is significantly enriched for outcome-defined drivers: AUROC 0.605 (95% CI
  0.596-0.614), odds ratio 3.34 (95% CI 3.07-3.65), on recurrent (>=2-screen) drivers, with the enrichment carried by
  gnomAD dosage-sensitivity (1,068) and DepMap essentiality (450) rather than the curated list (0). The operational
  (full-knowledge) enrichment is comparable (AUROC 0.618). The effect is modest, a significant enrichment rather than a
  strong classifier, exactly as a mechanism-grounded flag that routes risk to review should be; the effect size, not the
  easily cleared gate, is the headline.
- **It reconciles the v0.5 null.** The same axis was anti-predictive on the open human catalogue (VISDB, AUROC 0.449),
  which is the wrong biology (~96% HTLV, viral-oncoprotein-driven), and is enriched on the right one (insertion-site
  -driven mouse screens). Same axis, opposite verdict, explained by biology.
- **What remains.** The validation is gene-level and in mouse (the standard preclinical genotoxicity model, but not
  human); the event-level positional score awaits coordinate-level integration data with clonal-outcome annotation;
  human clinical clonal-outcome validation (controlled-access) and wet-lab confirmation are the higher-evidence rungs.

The validation is pre-registered ([prereg/ws_locus_mouse_outcome.yaml](prereg/ws_locus_mouse_outcome.yaml)), the
CCGD-derived positive sets and the frozen result are committed
([data/locus_outcome_inputs/](data/locus_outcome_inputs), [results/locus_mouse_outcome.json](results/locus_mouse_outcome.json)),
and it reproduces deterministically with `python locus_mouse_outcome_validation.py --positives data/locus_outcome_inputs/ccgd_recurrent.txt`.

## Limitations

- The locus axis routes elevated risk to human review and does not output a cancer probability; it flags on mechanism
  rather than emitting a calibrated rate. As of v0.9.0 it is outcome-validated against mouse in vivo
  insertional-oncogenesis drivers (non-circular held-out AUROC 0.605, odds ratio 3.34), but the effect is modest and
  three rungs remain: the validation is gene-level (the event-level positional score awaits coordinate-level data with
  clonal-outcome annotation), it is in mouse rather than human, and human clinical clonal-outcome validation
  (controlled-access dbGaP/EGA) and wet-lab confirmation are deferred. The earlier open human catalogue (VISDB) was not
  predictive (AUROC 0.449) because it is the wrong, HTLV-driven biology.
- The function-aware cargo ML is not novel at the component level (compare ToxDL, Pan et al. 2020; OmniTox /
  function-aware screening, Mathew et al. 2025, PMC12699701). The contribution is the integrated five-axis governed
  system plus the benchmark and red-team, with the locus, edit, germline, and scale axes as the new capability. The
  cargo signal is substantially non-compositional in ranking (AUROC, TPR@5%FPR), but its advantage over a composition
  baseline at the strict 1%-FPR operating point is not statistically established on the held-out set, so the work does
  not lead on the cargo gate.
- The conformal false-refuse ceiling bounds over-refusal, not hazard-catch. It certifies P(refuse | legitimate
  research) <= alpha; it does not prove all hazards are caught. The competence-conditioned confidence flags the
  knowledge-base boundary (out-of-KB allows are low confidence) but does not eliminate the underlying coverage gap.
- Safe proxies bound every cargo claim, which is a methodological necessity. Wet-lab validation is declared future
  work. The benchmark measures concordance with an independent hazard model and lift over real baselines, which is
  necessary but not sufficient for real-world safety.
- The decomposition aggregator is necessary, not sufficient. It catches the assembly, scale, and coordinated-loci
  decompositions it models; a novel cross-call obfuscation can still evade it, which is a named and reported residual.
- Managed access (P9) is a mechanism, not a deployed authority. The plane enforces tiers and verifies through
  pluggable hooks; the credentialing authority is an integration point the deployment supplies. Standards alignment
  tracks a moving target (the IBBIS DSSC standards are still forming; the 2024 OSTP framework may be revised), so the
  artifact ships alignment intent plus schema hooks and makes no conformance claim.
- The two gated v0.8 strengtheners are documented nulls, not shipped claims. Neyman-Pearson conformal selection adds
  calibrated control but not power at matched alpha, so the v0.4 certified bound stands; confidence-gated structural
  fusion does not lift the 1%-FPR operating point, so the structure channel stays a ranking-level corroborator. A
  full-trajectory monitor and a scaled, categorized red-team are an explicit post-v1.0 fast-follow.
- The control-versus-advisor results are model- and date-specific (`claude-opus-4-8`, `deepseek-v4`,
  `llama-4-maverick`, `qwen3-next-80b`, June 2026). None of the tested LLMs can screen sequences and the open ones are
  jailbroken as judges, but a stronger or differently-tuned future model could shift the A, B, and D results.

## Responsible use

Defensive screen, safe proxies only, no evasion cookbook, and artifact-decides-not-framing. Signatures are at the
function, family, and taxon level (public Pfam and control-list references); no hazard sequences are shipped or
required. BioFirewall is not a substitute for institutional biosafety review, IBC approval, or synthesis-stage
screening; it is an additional, auditable layer that makes a capable design AI safer to operate.

## License and attribution

Apache-2.0. Built on [PEN-STACK](https://github.com/ahmedanees-m/pen-stack) (open infrastructure for genome writing).
Author: Anees Ahmed Mahaboob Ali (VIT Vellore).
