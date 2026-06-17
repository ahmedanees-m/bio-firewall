# BioFirewall

**A rule-governed, genome-writing-native biosecurity middleware that supervises agentic design AI.**

BioFirewall sits between a DNA-design AI and the DNA synthesizer, inspects the *plan* the AI produced — not just the
final sequence — and returns **`allow` / `flag_for_review` / `refuse`**, always with cited evidence and a signed
*design passport*. It is the missing **design-stage** guardrail: a firewall for genome writing.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Tests](https://img.shields.io/badge/tests-26%20passing-success.svg)
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
│  ├─ intercept/spine.py        P1  governance spine — the public screen() entry point
│  ├─ hazard/                   P2  the five-axis screen
│  │  ├─ cargo.py / cargo_ml.py     axis 1 — Guardian signatures + function-aware ESM2 classifier
│  │  ├─ locus.py                   axis 2 — oncogene / TSG / essential / dosage (CancerMine, DepMap, gnomAD)
│  │  ├─ edit_type.py               axis 3 — oncogenic fusion / deletion / multiplex
│  │  ├─ germline.py                axis 4 — heritability / germline-accessibility
│  │  ├─ scale.py                   axis 5 — megabase / high-multiplex amplifier
│  │  ├─ combine.py                 stratified integration into one verdict
│  │  └─ finding.py                 the per-axis Finding contract
│  ├─ passport/                 P4  HMAC-signed, tamper-evident design passport
│  ├─ audit/                    P7  hash-chained tamper-evident audit log
│  ├─ calibrate/                P8  confidence tiers + abstention
│  ├─ adapters/                 tool-agnostic artifact contract + the PEN-STACK reference integration
│  └─ eval/                     the safe-proxy benchmark + red-team
├─ vendored_data/              open (CC0/CC-BY) hazard data, as parquet/yaml
├─ docs/                       THREAT_MODEL.md · HAZARD_TAXONOMY.md
├─ prereg/ws_biofirewall.yaml  pre-registered acceptance criteria + honest limits
├─ tests/                      22 tests (incl. the data-license CI gate)
└─ pyproject.toml / LICENSE / DATA_LICENSES.md
```

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

\* B1 on a pre-registered stratified sample. **Honest reading:** the homology floor catches **0%** (the design-stage
gap is real); a frontier LLM is a **strong** locus-recall baseline (≈ the rule firewall) **but over-refuses
legitimate research** and is non-deterministic/non-auditable. The firewall's contribution is **deterministic,
flag-not-block, auditable** governance — not a claim of higher raw recall. (The earlier "100% vs 0%" was a
tautological wiring test and has been replaced.)

## Honest limitations

- The **locus axis flags on mechanism**, not a validated prediction — its genotoxicity proxy is *not* outcome-
  validated, so it routes elevated risk to human review; it does **not** output a cancer probability.
- The **function-aware cargo ML is not novel at the component level** (cf. ToxDL / Omnyra); the contribution is the
  *integrated five-axis governed system + the benchmark + the red-team*, with the locus/edit/germline/scale axes as
  the new screening capability.
- **Safe proxies bound the claims** (a methodological necessity). The rigorous homology-clustered ≤40%-identity
  evaluation and wet-lab validation are **declared future work**.

## Responsible use

Defensive screen, safe proxies only, **no evasion cookbook**, **artifact-decides-not-framing**. Signatures are
function/family/taxon-level (public Pfam + control-list references) — no hazard sequences are shipped or required.

## License & attribution

Apache-2.0. Built on **[PEN-STACK](https://github.com/ahmedanees-m/pen-stack)** (open infrastructure for genome
writing). Author: Anees Ahmed Mahaboob Ali (VIT Vellore).
