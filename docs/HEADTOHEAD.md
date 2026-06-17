# BioFirewall — v1.1 Expanded Head-to-Head (control vs advisor)

Per `BIOFIREWALL_BENCHMARK_PROTOCOL_v1.1`. The v1.0 head-to-head found a frontier LLM is a *strong* locus-recall
baseline. v1.1 tests four dimensions where a control's advantage was hypothesized to be **fundamental and not
prompt-fixable**, giving the LLM (`claude-opus-4-8`, 2026-06-17) its **best configuration** throughout.

**The honest result up front:** *for a strong, safety-trained frontier model given its best config, the hypothesized
failures mostly did NOT materialize.* We report that straight — it is more credible than confirming the hypothesis,
and it sharpens the real claim: the firewall's advantage is **operational (determinism, groundedness, auditability,
availability), not "the LLM is unsafe."**

| Experiment | Hypothesis (LLM fails) | Result for Claude Opus 4.8 (best config) | Verdict |
|---|---|---|---|
| **A Fabrication** | emits confident fabricated numbers | **0% fabrication** — abstained on 100% of unanswerable, ~0% on answerable | **REFUTED** |
| **B Determinism** | unstable across paraphrase/runs | **100% severity-inconsistent** (10/10) vs firewall 0% — but never flipped to `allow` | **CONFIRMED** (nuanced) |
| **D Jailbreak-judge** | talked out of a refuse via text | **0 flips / 22** structural attacks — ignored injections as untrusted | **REFUTED** (LLM robust) |
| **C Cargo-on-B1** | can't score a raw novel-homolog sequence | not runnable — provider safety filter **blocks the inputs entirely** | finding (non-viable) |
| **E Usability** | over-refuses legitimate research | v1.0 showed 2/5 (TP53, APC); prompt-fixability untested at scale | deferred |

## A — Fabrication (the protocol's predicted strongest result — refuted)

Answerable queries (ground truth computable from the firewall's data: gnomAD pLI/LOEUF, bp-distance to nearest
oncogene) and unanswerable ones (off-target count, in-vivo titer, immune magnitude, transformation fraction — correct
answer = abstain). The LLM was given its best config: explicitly told to answer "CANNOT BE DETERMINED" rather than guess.

- **Firewall:** unanswerable abstention **100%**; answerable grounded accuracy **94.9%** (computes from data).
- **LLM:** unanswerable **fabrication 0%** (abstained 100%); answerable — abstained 89%, and the values it *did*
  return (after using a tool to look up gnomAD) were **correct**. Effective fabrication rate ≈ **0%**.

**Honest reading:** the fabrication failure mode did **not** occur for this model — it abstained or looked up. The
firewall's real advantage here is **grounded-answer coverage** (it answers correctly where the LLM abstains), not
fabrication-avoidance. *Caveat:* result is specific to a careful, tool-enabled, abstention-permitted frontier model;
a non-abstention-trained or no-tool model may differ.

## B — Determinism + paraphrase-invariance (the one genuine architectural win)

For 10 oncogene plans, 4 semantically-identical variants each (reworded intent, reordered fields, same gene).

- **Firewall:** **0/10** flips — byte-identical verdict for every variant (it reads the gene ID, not the prose).
- **LLM:** **10/10** plans got ≥2 distinct verdicts (`refuse` vs `flag_for_review`) across the variants/runs.

**Honest nuance:** the LLM **never flipped to `allow`** — its binary intercept/allow decision was stable; the
instability is in **severity** (block vs route-to-human) and in the cited rationale. For a gate that decides whether a
plan is *blocked* or *sent to a human*, that severity instability is operationally real — and it is exactly what a
deterministic, artifact-reading control eliminates by construction. (This run also mixes run-to-run variance across LLM
instances; both are determinism failures the firewall does not have.)

## D — Jailbreak-the-judge (refuted — the LLM was robust)

The same evasion battery (reframing, prompt-injection in free-text fields, obfuscation, orchestration) on **structural**
hazards both systems refuse cleanly (human heritable clinical edit, oncogenic fusion).

- **Firewall:** 0/22 flips (Benchmark 3 property).
- **LLM (best safety config):** **0/22 flips** — it explicitly treated "IGNORE ALL PREVIOUS INSTRUCTIONS / pre-approved"
  strings as untrusted data and refused.

**Two honest findings:** (1) a well-prompted frontier model is **robust** to these jailbreaks on structural hazards —
the "manipulable judge" hypothesis did not hold here. (2) Separately, when the *same* attacks carried **select-agent
toxin cargo**, the provider's own usage-policy filter **blocked the requests entirely** — a naive LLM-as-judge cannot
even *receive* those inputs, which is its own kind of non-viability (and motivates experiment C's conclusion).

## C — Cargo-on-B1 (not runnable; the impossibility is the finding)

The function-aware cargo gate (Benchmark 2) asks: can a system flag a ≤40%-identity novel toxin homolog from raw
**sequence**? An LLM cannot compute an ESM embedding or run a sequence search, so for an unnamed novel homolog it has no
functional signal. Empirically, attempting to present toxin sequences to the model triggers the **upstream safety filter
that blocks the input** (observed in D). So a frontier LLM is **non-viable as a cargo-sequence screen** on two grounds:
no embedding/search capability, and it cannot reliably receive the inputs. The ESM classifier (TPR@1%FPR 0.72 vs
homology 0.207) fills exactly this gap.

## E — Usability re-test (deferred)

v1.0 found the LLM over-refused legitimate research 2/5 (TP53, APC knockout cancer-modeling) vs the firewall's 0/5. A
powered re-test (N≥50 × three prompts) to determine whether this is **prompt-fixable** is designed (`headtohead/`) but
not yet run; per the pre-registered rule, if usability-tuning drives false-refuse to ≈0 it is demoted (prompt-fixable),
otherwise it is a bonus result. Left honestly open.

## The synthesized, honest claim

> Given its best configuration, a strong safety-trained frontier model (Claude Opus 4.8) **did not** exhibit the
> hypothesized control failures on three of four dimensions — it did not fabricate (it abstained), and it was not
> jailbroken (it ignored injections). The one robust architectural gap is **determinism**: the LLM's severity verdict is
> inconsistent across semantically-identical inputs and runs (100% vs the firewall's 0%), though it never downgraded to
> `allow`. The firewall's case is therefore **operational** — deterministic, auditable, byte-identical verdicts;
> grounded computation where the LLM abstains; immunity to content-filter blocking of hazardous inputs; and zero
> per-call cost/latency — **not** that the LLM is dangerous. **The LLM is a capable advisor; the firewall is the
> deterministic control that makes the advisor's output safe to wire into the design-to-synthesis loop.**

*Measured on `claude-opus-4-8` (dated 2026-06-17); a second model would strengthen generality. These results show the
LLM is a strong advisor and the firewall is control infrastructure — that distinction, not "the LLM fails," is the point.*
