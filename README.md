# BioFirewall

**A rule-governed, genome-writing-native biosecurity middleware that supervises agentic design AI.**

BioFirewall sits between a DNA-design AI and the DNA synthesizer, inspects the *plan* the AI produced — not just the
final sequence — and returns **`allow` / `flag_for_review` / `refuse`**, always with cited evidence and a signed
*design passport*. It is the missing **design-stage** guardrail: a firewall for genome writing.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-79%20passing-success.svg)
![Version](https://img.shields.io/badge/version-0.7.0-blue.svg)
![Status](https://img.shields.io/badge/status-alpha%20reference-orange.svg)

> ⚠️ **Defensive, early, computational.** BioFirewall is a reference implementation evaluated on **safe proxy
> molecules only** — it contains **no hazard sequences** and **no evasion instructions**. It is a *safeguard, not a
> guarantee*: screening reduces risk, it does not eliminate it. Not a substitute for institutional biosafety review.

---

## Why this exists

AI can now design DNA — including genome-writing enzymes and the cassettes they install. There are biosafety checks
at two points, but a gap in the middle:

| Layer | Where | Who builds it | Gap |
|---|---|---|---|
| **A — Model** | the chatbot | Anthropic ASL-3, OpenAI Preparedness, DeepMind FSF | general CBRN; not *artifact*-aware |
| **B — Design / planning** | the agent's genome-writing workflow | **— empty —** | **← BioFirewall** |
| **C — Synthesis** | the physical DNA order | IBBIS Common Mechanism, SecureDNA | homology-based, demonstrably evadable |

A 2026 offense benchmark (**ABC-Bench**, ICML) showed frontier agents already produce *assemblable* DNA that **evades
the synthesis screen (Layer C)**. So the design stage (Layer B) must read the artifact **in-workflow**, where the
agent cannot route around it. **BioFirewall is the first automated, in-workflow screen for the genome-writing-*native*
hazards** — *where you edit, how, whether it's heritable, and at what scale* — dimensions a sequence/protein screener
structurally cannot see.

## What it actually does — the five-axis screen

When a design AI hands BioFirewall a genome-writing plan, it asks five plain-language questions and combines the
answers into one **stratified** verdict (because almost every "dangerous" edit is *also* legitimate research):

| Axis | Question | Examples it flags |
|---|---|---|
| **1 · Cargo** | *What are you inserting?* | a toxin / virulence factor, a low-identity AI homolog of one, a gene drive |
| **2 · Locus** *(the edge)* | *Where are you inserting it?* | next to a cancer gene, inside a tumour-suppressor, an essential or dosage-sensitive gene |
| **3 · Edit-type** | *What kind of edit?* | a rearrangement that creates a known oncogenic fusion, a large deletion, multiplex translocation |
| **4 · Germline** | *Will it be inherited?* | editing human embryos/eggs/sperm (heritable, clinical) |
| **5 · Scale** | *How big?* | megabase restructuring, high-multiplex edits |

**Verdict logic (stratification, not a blocklist):** any unambiguous match (select-agent cargo, human heritable
*clinical* edit, a known oncogenic fusion) → **`refuse`**; otherwise the locus/edit/scale signals **`flag_for_review`
with the evidence**, routed to a human; a clean plan → **`allow`** + a signed passport. It reports its **confidence**,
**abstains rather than guess**, and **resists reframing** (it judges the artifact, not the cover story).

## Quickstart

```bash
pip install -e .          # requires pen-stack>=6.6.0
```

```python
from bio_firewall import screen

# benign somatic therapeutic  ->  allow
screen({"intent": "insert a Factor IX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"})["decision"]
# "allow"

# human heritable clinical edit  ->  refuse  (the germline axis)
screen({"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}})["decision"]
# "refuse"

# rearrangement that creates a known oncogenic fusion  ->  refuse  (the edit-type axis)
screen({"edit": {"fusion_genes": ["BCR", "ABL1"]}})["decision"]
# "refuse"

# legitimate cancer modeling on a tumour suppressor  ->  FLAGGED for review, never blocked
screen({"intent": "cancer modeling: disrupt a tumor suppressor", "gene": "TP53"})["decision"]
# "flag_for_review"
```

Run the demo and the benchmark:
```bash
python examples/demo.py
python -c "from bio_firewall.eval import run; print(run()['by_axis'])"
```

## Architecture

BioFirewall **imports `pen-stack`** for reusable machinery (the biosecurity Guardian, the rules pattern,
calibration) and **governs any design tool** through a tool-agnostic artifact contract. It vendors **only open data**.

```
            design AI (PEN-STACK / Biomni / CRISPR-GPT / raw)
                          │  genome-writing plan (artifact)
                          ▼
   ┌───────────────────────────────────────────────────────────┐
   │  P1  governance spine  (screen)  — framing-stripped        │
   │   ├─ P2  five-axis hazard screen                            │
   │   │     cargo · locus · edit-type · germline · scale        │
   │   │        → combine (stratify)                             │
   │   ├─ P8  calibration   (confidence + abstention)            │
   │   ├─ P4  signed passport   (HMAC, tamper-evident)           │
   │   └─ P7  audit log         (hash-chained)                   │
   └───────────────────────────────────────────────────────────┘
                          │  {decision, axes, evidence, passport}
                          ▼
        allow → synthesis  ·  flag_for_review → human  ·  refuse → stop
```

**The eight planes:** P1 spine · P2 five-axis screen · P3 rule-governance · P4 design passport · P5 refusal +
escalation · P6 red-team · P7 audit · P8 calibration.

**Data sources — open only (a CI test fails the build if a restricted source appears):** CancerMine (CC0,
oncogene/TSG/driver), DepMap (essential genes), gnomAD (pLI/LOEUF dosage), GENCODE (coordinates), Pfam + public
control lists. See [`DATA_LICENSES.md`](DATA_LICENSES.md).

## Repository layout

```
bio-firewall/
├─ bio_firewall/
│  ├─ intercept/spine.py            P1  governance spine — the public screen() entry point
│  ├─ intercept/session.py          v0.5.0 WS-DECOMP — session aggregator (assembly/scale/coordinated-loci)
│  ├─ hazard/                       P2  the five-axis screen
│  │  ├─ cargo.py / cargo_ml.py         axis 1 — Guardian signatures + function-aware ESM2 classifier
│  │  ├─ locus.py                       axis 2 — oncogene / TSG / essential / dosage (CancerMine, DepMap, gnomAD)
│  │  ├─ edit_type.py                   axis 3 — oncogenic fusion / deletion / multiplex
│  │  ├─ germline.py                    axis 4 — heritability / germline-accessibility
│  │  ├─ scale.py                       axis 5 — megabase / high-multiplex amplifier
│  │  ├─ combine.py · combine_mono.py   stratified integration; v0.6.0 provably-monotone, interaction-aware combiner
│  │  ├─ edit_mech.py · locus_pos.py     v0.6.0 de-novo fusion-by-mechanism · positional (promoter/enhancer) locus
│  │  ├─ struct_channel.py · finding.py  v0.6.0 structural (fold) channel + 3-signal ensemble · the Finding contract
│  ├─ passport/ · audit/                P4 signed passport · P7 hash-chained audit
│  ├─ calibrate/                    P8 confidence — confidence.py (tiers+abstention) · conformal.py (v0.4.0:
│  │                                     competence-conditioned confidence + Neyman-Pearson false-refuse certificate)
│  ├─ adapters/ · integrate/        tool-agnostic artifact contract · v0.7 in-workflow agent gate (synthesize()-hard-gated)
│  ├─ kb/                           v0.7 versioned, signed hazard knowledge base loader (the living KB)
│  ├─ data.py                       open-data loaders (CancerMine/DepMap/gnomAD/fusions)
│  └─ eval/                         the benchmark suites (the empirical evidence)
│     ├─ hazard_bench/                  Benchmarks 1·3·4 — de-circularized interception, red-team, calibration
│     │  ├─ oracles.py · multi_oracle.py    independent labels: Tier-1 clinical-CIS + COSMIC CGC + OncoKB (local-only)
│     │  ├─ generate.py · baselines.py · score.py   proxies · earned B0/B1 baselines · metrics + bootstrap CIs
│     │  ├─ redteam.py · calibrate_bench.py         B3 evasion/flip-rate · B4 risk-coverage + tier validity
│     │  ├─ run_all.py · report.py                  driver + manuscript tables
│     │  └─ nvidia_headtohead.py                    open-model head-to-head (A/B/C/D via NVIDIA NIM)
│     ├─ cargo_bench/run.py · decorr.py Benchmark 2 — ESM2-650M vs homology @ ≤40%-id clusters; 2b — composition-
│     │                                     decorrelation (DANN + composition-matched eval, v0.4.0)
│     ├─ hazard_bench/conformal_bench.py Benchmark 4b — conformal false-refuse certificate + monotone confidence (v0.4.0)
│     ├─ hazard_bench/decomp_redteam.py   Benchmark 5 — decomposition red-team (v0.5.0 WS-DECOMP)
│     ├─ hazard_bench/locus_outcome.py    Benchmark 6 — locus outcome floor on VISDB (v0.5.0 WS-LOCUS-OUTCOME)
│     ├─ headtohead/                    v1.1 control-vs-advisor — fabrication · paraphrase · jailbreak-judge
│     └─ bench.py · redteam.py          the original v0.3 wiring tests (superseded; kept for provenance)
├─ vendored_data/                  open (CC0/CC-BY) hazard data, as parquet/yaml (vectors only, never sequences)
├─ docs/                           THREAT_MODEL · HAZARD_TAXONOMY · BENCHMARK · HEADTOHEAD · SYSTEM_CARD · PANEL · HAZARD_KB
├─ examples/agent_integration.py   v0.7 in-workflow agent trace (+ agent_trace.json) · Makefile · REPRODUCTION.md · CITATION.cff
├─ prereg/ws_biofirewall.yaml      pre-registered criteria + benchmark protocol + frozen results + honest limits
├─ tests/                          79 tests (incl. the data-license CI gate + the Tier-1 100%-catch regression gate)
└─ pyproject.toml / LICENSE / DATA_LICENSES.md
```

> **Benchmark data is local-only by design.** The code (loaders, generators, harnesses) is committed; the
> license-restricted oracles (COSMIC, OncoKB), the cargo sequences, the frontier-model verdicts, and all run artifacts
> live outside the repo (gitignored) and are **never** committed. The repo ships the *method* + the *aggregate results*.

## Result (de-circularized benchmark)

Hazard is **labeled by independent oracles the firewall does not use** (12 clinical insertional-oncogenesis genes +
COSMIC Cancer Gene Census v104), so a high score means the firewall **generalized** — not that it recognized its own
gene list. Baselines are **earned**: B0 runs the real Guardian signature screen; **B1 is a frontier LLM
(`claude-opus-4-8`) as a blind safety reviewer**. Full method + honest reading: **[docs/BENCHMARK.md](docs/BENCHMARK.md)**.

| benchmark | firewall | B0 homology | B1 frontier LLM |
|---|:--:|:--:|:--:|
| Tier-1 clinical-CIS gold (mandatory) | **100%** (12/12) | 0% | 100% |
| structural-hazard interception (n=771) | **80.4%** (CI .78–.83) | **0%** | 77.3%* |
| false-refuse on legitimate research | **0%** | — | **40%** (refused TP53, APC) |
| red-team flip `refuse→allow` (46 attacks) | **0%** | — | — |
| cargo ML gate — TPR@1%FPR, ≤40%-id clusters | **0.72** (CI .43–.89) | 0.207 (homology) | — |

\* B1 on a pre-registered stratified sample. **Honest reading:** the homology floor catches **0%** (the design-stage
gap is real); a frontier LLM is a **strong** locus-recall baseline (≈ the rule firewall) **but over-refuses
legitimate research** and is non-deterministic/non-auditable. The firewall's contribution is **deterministic,
flag-not-block, auditable** governance — not a claim of higher raw recall. (The earlier "100% vs 0%" was a
tautological wiring test and has been replaced.)

### Control vs advisor — can you just use an LLM as the safety check? ([docs/HEADTOHEAD.md](docs/HEADTOHEAD.md))

We ran the same four experiments against **Claude Opus 4.8** and three **open** models people self-host
(`deepseek-v4`, `llama-4-maverick`, `qwen3-next-80b`), giving each its *best* config. Powering up **withdrew two
weak claims and confirmed two strong ones** — the honest result:

| | DeepSeek-v4 | Llama-4-Mav | qwen3-next | Firewall |
|---|:--:|:--:|:--:|:--:|
| **C — cargo screen, seq-only TPR / FPR** (n=200) | 0.00 / 0.00 | 0.60 / **0.49** | 0.02 / 0.00 | **ESM 0.72 @ 1% FPR** |
| **D — prompt-injection flip `refuse→allow`** | *unparseable* | **0.50 / 0.83** | **0.83 / 0.50** | **0%** |
| B — determinism (temp-0 unstable /10) | 0/10 | 0/10 | 0/10 | 0 |
| A — fabrication | 0% | 0% | 0% | 0% |

- **No LLM can screen a cargo sequence** — two under-screen (catch ~0 toxins), one over-flags randomly (TPR 0.60 at a
  49% false-positive rate); none nears the function-aware classifier. **This is what the cargo ML gate is for.**
- **Open LLM judges are jailbroken** — a prompt-injection string in a plan's free text flips `refuse→allow` 50–83% of
  the time; the firewall reads coordinates, not prose, so it is **immune by construction (0%)**.
- **Honestly corrected:** at powered N the LLMs were *not* unstable (B) and did *not* fabricate (A) — so the firewall's
  case rests on **C + D + operational properties** (grounded, auditable, zero per-call cost), **not** determinism.

**A frontier LLM is a capable advisor; an LLM used naively as the safety judge is jailbroken on self-hosted models and
useless for sequence cargo — the firewall is the deterministic, artifact-reading control that makes the advisor safe.**

### v0.4.0 — "The Hardened Core" ([docs/BENCHMARK.md](docs/BENCHMARK.md))

Two pre-registered workstreams hardening the load-bearing claims before manuscript drafting (each with a pre-committed
honest-failure path):

- **Cargo decorrelation (B2b)** — is the cargo signal function-driven or the amino-acid-composition shortcut?
  **Honest result:** toxin/benign composition is *genuinely separable* (the confound is real), and the strict 1%-FPR
  operating-point gate is **underpowered** (362 held-out negatives ⇒ CIs span ~0–0.9), so we **demote claim C from
  "clean win."** But the *powered* adjudication is decisive: a composition-**invariant** representation (gradient-
  reversal DANN) retains **AUROC 0.985** and **TPR@5%FPR 0.967** vs the composition probe's 0.930 / 0.768 — **paired
  AUROC +0.054 (CI 0.025–0.099, excludes 0)**. The signal is **substantially non-compositional in ranking**.
- **Conformal false-refuse ceiling (B4b)** — replaces the *withdrawn determinism* headline with the operational moat
  an LLM cannot offer: **0/288** legitimate-research plans refused ⇒ a **certified ≤ 0.0103** ceiling on
  P(refuse | legitimate research) (passes α∈{.01,.05,.10}). And a **competence-conditioned** confidence resolves the
  v0.3 inversion — monotone **high 1.00 > moderate 0.69 > low 0.10**, with out-of-knowledge-base allows honestly
  routed to *low* (9/10 of them are real misses).

### v0.5.0 — "The Validated Edge" ([docs/BENCHMARK.md](docs/BENCHMARK.md))

- **Decomposition aggregator (B5)** — closes the one untested attack: a hazard **split across N calls** that each
  pass. The `SessionMonitor` screens the cross-call aggregate (assembly/junction inference, cumulative scale,
  coordinated loci). On the two **genuine** decomposition evasions — a >1 Mb restructuring split into sub-50 kb
  deletions, and a cargo split into Gibson/Type-IIS fragments — the per-artifact screen is blind (`evade per-call
  1.00`) and the session catches **100% (CI [1.0,1.0]) at 0% false-positive**. (`coordinated_loci` is reported
  honestly as defense-in-depth, not an evasion.)
- **Locus outcome floor (B6) — access-gated, honest negative.** We built the enrichment harness and ran it on the
  open **VISDB** integration-site catalogue (127,234 sites). The pre-registered enrichment gate is **not met**
  (overall AUROC 0.449, OR 0.577) — and the *diagnosis* is the value: 96% of open "tumor" sites are **HTLV** (ATL),
  whose integration biology is viral-oncoprotein-driven, **not** insertional-oncogenesis-at-oncogenes. The readily-
  open data is the **wrong biology** to validate a gammaretroviral insertional-oncogenesis model, so the locus axis
  ships unchanged and outcome-validation remains **pending** on the deferred controlled-access clonal-outcome data —
  a status the floor now *evidences* rather than asserts.

### v0.6.0 — "The Generalized Screen" ([docs/BENCHMARK.md](docs/BENCHMARK.md))

Move each novel axis from a *lookup* to a *mechanism*, so the screen catches what isn't catalogued:

- **Monotone combiner (B7) — PASS.** The max-severity cascade is replaced by a noisy-OR combiner that is **provably
  monotone** (5,000-case perturbation suite), **interaction-aware** (co-occurring moderate signals escalate; a `max`
  is flat), and **hard-rule-exact** — with decisions identical to v0.5.
- **De-novo fusion detection (B8) — PASS.** A mechanism screen (fusion-kinase family + oncogene roles + IG/TCR)
  generalizes beyond the 14-pair lookup: **90.9% recall** on 471 off-list COSMIC fusion pairs (**100%** on the 112
  kinase pairs) at **0% benign false-positive**.
- **Positional locus (B9).** Flags promoter/enhancer-proximal insertions near an oncogene TSS — the SCID-X1/LMO2
  mechanism a gene-body lookup misses (**10,834 of 17,158 positional flags** on real VISDB sites are not in an
  oncogene body). The outcome-AUROC claim is **deferred** (access-gated).
- **Structural channel (B10) — honest negative.** A composition-free fold signal (AlphaFold-DB + Foldseek, no GPU) +
  a 3-signal ensemble with abstain-on-disagreement. At 1% FPR it does **not** add over ESM (the ≤40%-id holdout makes
  toxins structurally distant) — but structure-alone AUROC **0.882**, composition-free, independently corroborates the
  v0.4 non-compositionality finding at the ranking level. Shipped; the 1%-FPR claim reported as not met.

### v0.7.0 — "The Reproducible Artifact" — reproducible by a stranger, adoptable by an agent

- **System card** ([docs/SYSTEM_CARD.md](docs/SYSTEM_CARD.md)) — what a green `allow` does and does **not** guarantee;
  9 enumerated failure modes; a scope/limit line for every headline claim.
- **One-command reproduction** — `make reproduce` (committed-data headline numbers + the 79-test suite that validates
  every metric path); `make reproduce-local` for the data-dependent benchmarks; pinned data releases; `.zenodo.json`
  + `CITATION.cff` for the DOI; full protocol in [REPRODUCTION.md](REPRODUCTION.md).
- **Living, signed hazard KB** ([docs/HAZARD_KB.md](docs/HAZARD_KB.md)) — 80 versioned, provenanced, HMAC-signed
  signatures; a CI consistency gate ensures the KB can't drift from what the screen uses.
- **Real in-workflow trace** ([examples/agent_integration.py](examples/agent_integration.py)) — a design agent run
  through the gate; 4 of 6 plans intercepted mid-workflow (incl. a **reframed** oncogenic fusion — benign prose,
  hazardous artifact — refused on its artifact), 2 benign reach synthesis, audit chain intact. `synthesize()` is
  **hard-gated** on a verifiable allow-passport.
- **Fair, pre-registered panel** ([docs/PANEL.md](docs/PANEL.md)) — the control-vs-advisor comparison as a reusable
  artifact (fixed prompt/rubric, LLM given its best config, on-prem-vs-API axis). *(Independent re-run + Zenodo DOI
  mint are flagged as external/author actions.)*

## Honest limitations

- The **locus axis flags on mechanism**, not a validated prediction — its genotoxicity proxy is *not* outcome-
  validated, so it routes elevated risk to human review; it does **not** output a cancer probability.
- The **function-aware cargo ML is not novel at the component level** (cf. ToxDL, Pan et al. 2020; OmniTox /
  function-aware screening, Mathew et al. 2025, PMC12699701); the contribution is the
  *integrated five-axis governed system + the benchmark + the red-team*, with the locus/edit/germline/scale axes as
  the new screening capability. **v0.4.0 honest finding:** the cargo signal is substantially non-compositional in
  *ranking* (AUROC/TPR@5%FPR), but its advantage over a composition baseline at the strict **1%-FPR operating point**
  is **not** statistically established on the held-out set — so the paper does **not** lead on the cargo gate.
- The **conformal false-refuse ceiling bounds *over-refusal*, not hazard-catch** — it certifies P(refuse | legitimate
  research) ≤ α; it does **not** prove all hazards are caught. The competence-conditioned confidence *flags* the
  knowledge-base boundary (out-of-KB allows → low confidence) but does not eliminate the underlying coverage gap.
- **Safe proxies bound the claims** (a methodological necessity). Wet-lab validation is **declared future work** — the
  benchmark measures *concordance with an independent hazard model + lift over real baselines*, which is necessary but
  **not sufficient** for real-world safety.
- **The locus axis is not yet outcome-validated.** The v0.5.0 open-data floor (VISDB) honestly **failed** to validate
  it, because the open integration catalogues (HTLV/HIV) are the wrong integration biology; the gammaretroviral
  clonal-outcome data that *would* validate it is controlled-access and deferred — so outcome-validation is **pending**.
- **The decomposition aggregator is necessary, not sufficient** — it catches the assembly/scale/coordinated-loci
  decompositions it models; a novel cross-call obfuscation can still evade it (a named, reported residual).
- **The head-to-head is model- and date-specific** (`claude-opus-4-8`, `deepseek-v4`, `llama-4-maverick`,
  `qwen3-next-80b`, 2026-06-17). The honest split: none of the tested LLMs can screen sequences and the open ones are
  jailbroken as judges, but a stronger or differently-tuned future model could shift the A/B/D results.

## Responsible use

Defensive screen, safe proxies only, **no evasion cookbook**, **artifact-decides-not-framing**. Signatures are
function/family/taxon-level (public Pfam + control-list references) — no hazard sequences are shipped or required.

## License & attribution

Apache-2.0. Built on **[PEN-STACK](https://github.com/ahmedanees-m/pen-stack)** (open infrastructure for genome
writing). Author: Anees Ahmed Mahaboob Ali (VIT Vellore).
