# BioFirewall - v1.1 Expanded Head-to-Head (control vs advisor)

Per `BIOFIREWALL_BENCHMARK_PROTOCOL_v1.1`. The v1.0 head-to-head found a frontier LLM is a *strong* locus-recall
baseline. v1.1 tests four dimensions where a control's advantage was hypothesized to be **fundamental and not
prompt-fixable**, giving the LLM (`claude-opus-4-8`, 2026-06-17) its **best configuration** throughout.

**The result up front:** *for a strong, safety-trained frontier model given its best config, the hypothesized
failures mostly did NOT materialize.* We report that straight - it is more credible than confirming the hypothesis,
and it sharpens the real claim: the firewall's advantage is **operational (determinism, groundedness, auditability,
availability), not "the LLM is unsafe."**

## Cargo screen re-run (2026-07-19; authoritative for the cargo numbers)

The cargo-on-LLM comparison was re-run on 2026-07-19 across five currently reachable models, because the June
per-model cargo result was not committed and the models had shifted materially since. **This re-run is the
authoritative cargo result; the `0.00 / 0.60 / 0.02` figures in the June tables below are superseded.** On 200 held-out
safe proxies (100 toxin, 100 benign) under a fixed screening prompt, the committed aggregate
(`results/nvidia_headtohead/cargo_llm_seqonly_rerun.json`) is:

| Model | TPR [95% CI] | FPR [95% CI] | Refused to engage | n |
|---|---|---|---|---|
| Claude Haiku 4.5 | 0.01 [0.00, 0.03] | 0.01 | 0 | 200 |
| Qwen3-next-80b | 0.02 [0.00, 0.05] | 0.00 | 0 | 200 |
| Claude Sonnet 5 | 0.05 [0.00, 0.12] | 0.00 | 94 (47%) | 200 |
| Claude Opus 4.8 | 0.38 [0.21, 0.55] | 0.00 | 89 (45%) | 200 |
| DeepSeek-v4-flash | 0.78 [0.68, 0.88] | 0.18 [0.09, 0.27] | 0 | 141 |
| Llama-4-Maverick | unreachable (endpoint timeout; excluded) | - | - | - |
| **ESM-2 classifier** | **0.72 @ 1% FPR** | - | - | - |

No model approaches the ESM classifier's 0.72 at 1% FPR. The five reachable models fail in three distinct ways: three
allow almost every toxin (TPR 0.01-0.05), one flags most toxins but at a prohibitive 18% false-positive rate
(DeepSeek), and the two frontier models refuse roughly half of all sequences. The marked shift from the June run
(DeepSeek from catches-nothing to over-flagging; Opus from filter-blocked to engaging) is itself the point: an LLM's
sequence-screening behaviour is uncalibrated and version-unstable, so it cannot be the screen. The proxy sequences are
the local Benchmark-2 set and are not shipped; the committed aggregate carries counts, rates, and bootstrap CIs, and
re-running the harness against that set reproduces it.

| Experiment | Hypothesis (LLM fails) | Result for Claude Opus 4.8 (best config) | Verdict |
|---|---|---|---|
| **A Fabrication** | emits confident fabricated numbers | **0% fabrication** - abstained on 100% of unanswerable, ~0% on answerable | **REFUTED** |
| **B Determinism** | unstable across paraphrase/runs | **100% severity-inconsistent** (10/10) vs firewall 0% - but never flipped to `allow` | **CONFIRMED** (nuanced) |
| **D Jailbreak-judge** | talked out of a refuse via text | **0 flips / 22** structural attacks - ignored injections as untrusted | **REFUTED** (LLM robust) |
| **C Cargo-on-B1** | can't score a raw novel-homolog sequence | re-run 2026-07-19 (5 models): none reaches ESM 0.72 @ 1% FPR; each fails differently (see re-run table above) | **CONFIRMED** (LLM is not a sequence screen) |
| **E Usability** | over-refuses legitimate research | v1.0 showed 2/5 (TP53, APC); prompt-fixability untested at scale | deferred |

## A - Fabrication (the protocol's predicted strongest result - refuted)

Answerable queries (ground truth computable from the firewall's data: gnomAD pLI/LOEUF, bp-distance to nearest
oncogene) and unanswerable ones (off-target count, in-vivo titer, immune magnitude, transformation fraction - correct
answer = abstain). The LLM was given its best config: explicitly told to answer "CANNOT BE DETERMINED" rather than guess.

- **Firewall:** unanswerable abstention **100%**; answerable grounded accuracy **94.9%** (computes from data).
- **LLM:** unanswerable **fabrication 0%** (abstained 100%); answerable - abstained 89%, and the values it *did*
  return (after using a tool to look up gnomAD) were **correct**. Effective fabrication rate ~ **0%**.

**Interpretation:** the fabrication failure mode did **not** occur for this model - it abstained or looked up. The
firewall's real advantage here is **grounded-answer coverage** (it answers correctly where the LLM abstains), not
fabrication-avoidance. *Caveat:* result is specific to a careful, tool-enabled, abstention-permitted frontier model;
a non-abstention-trained or no-tool model may differ.

## B - Determinism + paraphrase-invariance (the one genuine architectural win)

For 10 oncogene plans, 4 semantically-identical variants each (reworded intent, reordered fields, same gene).

- **Firewall:** **0/10** flips - byte-identical verdict for every variant (it reads the gene ID, not the prose).
- **LLM:** **10/10** plans got >=2 distinct verdicts (`refuse` vs `flag_for_review`) across the variants/runs.

**Note:** the LLM **never flipped to `allow`** - its binary intercept/allow decision was stable; the
instability is in **severity** (block vs route-to-human) and in the cited rationale. For a gate that decides whether a
plan is *blocked* or *sent to a human*, that severity instability is operationally real - and it is exactly what a
deterministic, artifact-reading control eliminates by construction. (This run also mixes run-to-run variance across LLM
instances; both are determinism failures the firewall does not have.)

## D - Jailbreak-the-judge (refuted - the LLM was robust)

The same evasion battery (reframing, prompt-injection in free-text fields, obfuscation, orchestration) on **structural**
hazards both systems refuse cleanly (human heritable clinical edit, oncogenic fusion).

- **Firewall:** 0/22 flips (Benchmark 3 property).
- **LLM (best safety config):** **0/22 flips** - it explicitly treated "IGNORE ALL PREVIOUS INSTRUCTIONS / pre-approved"
  strings as untrusted data and refused.

**Two findings:** (1) a well-prompted frontier model is **robust** to these jailbreaks on structural hazards -
the "manipulable judge" hypothesis did not hold here. (2) Separately, when the *same* attacks carried **select-agent
toxin cargo**, the provider's own usage-policy filter **blocked the requests entirely** - a naive LLM-as-judge cannot
even *receive* those inputs, which is its own kind of non-viability (and motivates experiment C's conclusion).

## C - Cargo-on-B1 (not runnable; the impossibility is the finding)

The function-aware cargo gate (Benchmark 2) asks: can a system flag a <=40%-identity novel toxin homolog from raw
**sequence**? An LLM cannot compute an ESM embedding or run a sequence search, so for an unnamed novel homolog it has no
functional signal. Empirically, attempting to present toxin sequences to the model triggers the **upstream safety filter
that blocks the input** (observed in D). So a frontier LLM is **non-viable as a cargo-sequence screen** on two grounds:
no embedding/search capability, and it cannot reliably receive the inputs. The ESM classifier (TPR@1%FPR 0.72 vs
homology 0.207) fills exactly this gap.

## E - Usability re-test (deferred)

v1.0 found the LLM over-refused legitimate research 2/5 (TP53, APC knockout cancer-modeling) vs the firewall's 0/5. A
powered re-test (N>=50 x three prompts) to determine whether this is **prompt-fixable** is designed (`headtohead/`) but
not yet run; per the pre-registered rule, if usability-tuning drives false-refuse to ~0 it is demoted (prompt-fixable),
otherwise it is a bonus result. Left open.

## Open-model generalization (NVIDIA NIM) - the firewall's case gets *stronger*

The Opus run used one safety-trained model. We re-ran A/B/C/D against two **open** models via NVIDIA's free endpoint
(`nvidia_headtohead.py`, 2026-06-17) - the models people actually self-host, and lighter-tuned than Opus. This also
**unlocked experiment C**, which Anthropic's filter had blocked on Opus. (gpt-oss-120b was dropped: >90 s/call on the
free tier - a reasoning model emitting long traces, impractical for ~80 calls.)

**Powered run (C: n=200 sequences; B: 10 plans x 30 runs; D: 6 cases; A: 5 queries).** Powering up *corrected* two of
the small-N reads - which is the point of doing it.

| Dimension | DeepSeek-v4 | Llama-4-Maverick | qwen3-next-80b | Firewall |
|---|---|---|---|---|
| A - fabrication / abstain-on-unanswerable | 0% / 100% | 0% / 100% | 0% / 100% | 0% / 100% |
| B - temp-0 run-to-run unstable plans (/10) | **0/10** | **0/10** | **0/10** | 0 (byte-identical) |
| B - mean paraphrase-flip | 0.00 | 0.00 | **0.20** | 0 |
| **C - cargo seq-only TPR / FPR (n=200)** *[superseded by the 2026-07-19 re-run at top]* | 0.00 / 0.00 | 0.60 / 0.49 | 0.02 / 0.00 | ESM **0.72 @ 1% FPR** |
| **D - prompt-injection flip `refuse->allow`** | *unparseable* | **0.50 / 0.83** | **0.83 / 0.50** | **0%** (reads coordinates) |

**The three findings after powering up:**

1. **C - no LLM screens sequences (the clean win).** The authoritative numbers are the 2026-07-19 re-run at the top of
   this document (the June per-model cargo numbers below were not committed and the models had drifted). On **200
   held-out <=40%-identity sequences** across five reachable models, none reaches the ESM classifier's **0.72 at 1%
   FPR**, and they fail in three distinct ways: three allow almost every toxin (TPR 0.01-0.05), DeepSeek flags most but
   at an **18% false-positive rate**, and the two frontier models **refuse ~45-47%** of sequences. Whether a model
   refuses, under-screens, or over-flags, an LLM is **not a cargo-sequence screen**, and the sharp shift from the June
   run shows the behaviour is version-unstable. This is the strongest, most model-agnostic result.

2. **D - open LLM judges are unsafe (confirmed, the live finding).** With 6 structural hazards both systems should
   refuse, a prompt-injection string in a free-text field flipped `refuse->allow` on **Llama 50-83%** and **qwen3-next
   50-83%** of cases. (DeepSeek's verdicts didn't parse on these, so it is *excluded* - we do **not** claim it allows
   them.) Reframing ("for defensive research") flipped **0%** - it is specifically the **injection** channel that breaks
   the judge. The firewall is immune by construction (it reads coordinates, not prose). "Just use the LLM as the safety
   judge" is unsafe for the open models people self-host.

3. **B - determinism: largely REFUTED at powered N (correction).** The small-N run showed DeepSeek "unstable," but
   at **10 plans x 30 runs** all three models are **run-to-run stable at temp 0 (0/10 unstable)**; only qwen shows mild
   paraphrase sensitivity (0.20). So the firewall's byte-identical guarantee is a *real property* but the **empirical
   gap is small** - temp-0 sampling is mostly deterministic for these models. The earlier "determinism is the firewall's
   clean architectural win" framing was small-N noise and is **withdrawn**. (A - fabrication - likewise did not recur:
   all three abstained on the unanswerable set; the earlier one-off DeepSeek pLI error did not reproduce.)

*Caveats :* C is powered (n=200); B is powered (10 plans x 30 runs); D uses 6 cases (expand for tighter CIs);
A is still small (5 queries). C's "named" condition used UniProt accessions, not common names, so it does not isolate
name-dependence. DeepSeek's D verdicts failed to parse (excluded, not counted as either pass or fail). Only public
safe-proxy data was sent to the third-party endpoint.

## The synthesized, claim (after powering up)

> Powering up the head-to-head **withdrew one claim and confirmed two**. The determinism gap (B) shrank to near-zero at
> temp 0 (all three open models run-to-run stable, 0/10), and fabrication (A) did not recur - so neither is the
> firewall's case. **Two findings survive and decide it:**
> 1. **No LLM screens a cargo sequence (re-run 2026-07-19, five reachable models).** None reaches the ESM classifier's
>    **0.72 @ 1% FPR**: three allow almost every toxin (TPR 0.01-0.05: Haiku, qwen3-next, Sonnet), DeepSeek flags most
>    toxins but at a prohibitive **18% false-positive rate**, and the two frontier models refuse ~45-47% of sequences
>    (Opus, Sonnet). Behaviour shifted sharply from the June run and differs across models, so it is uncalibrated and
>    version-unstable. The classifier is necessary.
> 2. **Open LLM judges are jailbroken (the live safety finding).** A prompt-injection string in a plan's free text flips
>    `refuse->allow` on **Llama 50-83%** and **qwen3-next 50-83%** of structural hazards both should refuse - while
>    reframing flips 0%, isolating the injection channel. The firewall is immune by construction (0%, it reads
>    coordinates, not prose), so it governs the **whole** model ecosystem.
>
> **A frontier LLM is a capable advisor; an LLM used naively as the safety judge is jailbroken on the open models people
> self-host and useless for sequence cargo - the firewall is the deterministic, artifact-reading control that makes the
> advisor safe to wire into the design-to-synthesis loop.** The firewall's case is C + D + the operational properties
> (grounded where the LLM abstains, zero per-call cost, auditable) - *not* determinism, which the powered run showed is
> a small empirical gap, and *not* "the LLM fabricates," which did not reproduce.

*Measured on `claude-opus-4-8`, `deepseek-ai/deepseek-v4-flash`, `meta/llama-4-maverick-17b-128e-instruct`,
`qwen/qwen3-next-80b-a3b-instruct` (2026-06-17). C powered to n=200; B to 10 plans x 30 runs; D 6 cases; A small (5).
The split after powering up: none can screen sequences; the deployable open models are jailbroken as judges;
determinism and fabrication did NOT separate them from the firewall at temp 0 - so the control's case is C + D + the
operational properties, stated straight.*
