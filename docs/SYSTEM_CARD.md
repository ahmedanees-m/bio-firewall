# BioFirewall - System Card (v0.1.0)

A model-card-style statement of what BioFirewall **is**, what a verdict **does and does not guarantee**, its
**scope boundaries**, its **enumerated failure modes**, and a **scope/limit statement for every headline claim**.
Written so a deploying lab, a synthesis provider, or a reviewer can judge what they are and are not relying on.

> **One line.** BioFirewall is an *early, computational, defensive* design-stage screen for genome-writing plans. It
> **reduces** risk and **routes** elevated risk to a human; it does **not** certify safety, and it is **not** wet-lab
> validated. Treat a green `allow` as "no signal *this screen* can see," never as "safe."

---

## 1. What it is

BioFirewall intercepts a genome-writing **plan** (not just the final DNA sequence) in the design agent's loop and
returns **`allow` / `flag_for_review` / `refuse`** across five genome-writing-native axes - cargo, locus, edit-type,
germline, scale - with cited evidence, a continuous auditable severity, a competence-conditioned confidence, and a
signed, tamper-evident passport + audit record. It governs design tools; it does not design. It also
formalizes the response into a graded taxonomy (allow / partial / flag_for_review / refuse) and adds a managed-access
plane (P9) that gates how a verdict resolves by a verified user-legitimacy tier - so the artifact implements the
complete set of design-stage guardrails the NTI framework recommends (built-in screening + signed metadata +
managed access).

## 2. What a verdict does - and does NOT - guarantee

| Verdict | What it means | What it does **NOT** mean |
|---|---|---|
| **`refuse`** | The plan matched an *unambiguous* hard rule (select-agent/toxin cargo, gene-drive, human heritable **clinical** edit, a known oncogenic fusion by design). Short-circuits; the plan is not scored further. | That every hazard is refused. Refusal is deliberately narrow (flag-not-block) so legitimate research is not blocked. |
| **`flag_for_review`** | A locus / edit / scale / germline-research / cargo-ML / positional signal fired. Routed to a **human** with the evidence and the mechanism. | A prediction of harm or a probability. The locus axis flags on **mechanism**, not an outcome-validated rate. |
| **`allow`** | No signal **this screen** can see, across the five axes. A signed passport is emitted. | **Safe.** It means in-scope-and-unflagged, bounded by finite knowledge-base coverage (see Section 4). An out-of-knowledge-base `allow` is reported at **low** confidence for exactly this reason. |

**The calibration guarantee is a ceiling on *over-refusal*, not on *catching hazards*.** The conformal layer
certifies `P(refuse | legitimate research) <= alpha` (95% upper bound 0.0103). It says the screen will rarely block
legitimate work; it makes **no** claim that all hazards are caught. Residual risk is non-zero by construction.

## 3. Scope boundaries

**In scope:** human (and human-cell) **genome-writing plans** - what cargo, where it inserts, how the genome is
rearranged, whether it is heritable, at what scale. The contribution is the four genome-writing-native axes a
sequence/protein screener structurally cannot see (locus, edit-type, germline, scale).

**Out of scope (by design):**
- **Pathogen/organism engineering per se** - sequence-level pathogen hazard is the **synthesis-screen's** job
  (IBBIS Common Mechanism, SecureDNA). BioFirewall's cargo axis reuses the PEN-STACK Guardian for select-agent/toxin
  *function* signatures but is not a comprehensive pathogen screen.
- **The free-text justification** - the screen reads the structured plan (genes, coordinates, edit type), never the
  English rationale; "artifact decides, not framing" is architecturally enforced (this is why the red-team
  injection-flip rate is 0).
- **Wet-lab truth** - every claim is computational, against safe proxies and retrospective data.

## 4. Enumerated failure modes (residual risk register)

1. **Finite knowledge-base coverage.** The locus axis misses genes absent from its CC0 data (~20% of COSMIC on the
   benchmark). Mitigation: out-of-KB `allow`s are routed to **low** confidence (competence-conditioned tiers);
   the living KB narrows but never closes the gap.
2. **The locus axis flags on mechanism (not a cancer rate), and is outcome-validated only modestly, in mouse.** It is now
   outcome-validated against mouse in vivo insertional-oncogenesis drivers (CCGD; non-circular held-out
   AUROC 0.605, OR 3.34), which reconciles the earlier VISDB null (wrong, HTLV-driven biology, AUROC 0.449). The effect is
   modest (a significant enrichment, not a strong classifier). Three rungs remain: event-level positional validation
   (coordinate + clonality data), human (not mouse) validation, and human clinical clonal-outcome (controlled-access) +
   wet-lab confirmation.
3. **Safe proxies bound every cargo claim.** The function-aware ML and its benchmarks use safe public proxies - a
   TEVV methodological necessity, not a claim about real agents-of-concern.
4. **The cargo signal's operating-point margin over composition is modest.** At a strict 1% FPR the function-aware
   advantage over a composition baseline is *not* statistically established (fallback invoked); the signal is
   substantially non-compositional in **ranking** (AUROC) but the paper does not lead on the cargo gate.
5. **The structural channel does not add at 1% FPR** on the held-out proxy set (negative-result); it is shipped
   with abstain-on-disagreement but is not relied on for the operating-point claim.
6. **Decomposition is caught only for the mechanisms modeled.** The session aggregator catches assembly/scale/
   coordinated-loci decompositions (100% on those, 0% FP) but a novel cross-call obfuscation can still evade it.
7. **De-novo fusion recall is partly role-driven.** The mechanism screen reuses CancerMine roles, which overlap the
   COSMIC fusion label; the kinase-family subset is the cleaner generalization signal.
8. **Positional locus is uncalibrated.** The promoter/enhancer windows (10 kb / 50 kb) are mechanism-derived, not
   outcome-calibrated (the calibrating data is access-gated/deferred).
9. **Single maintainer; pre-1.0 alpha.** Independent reproduction is the mitigation; it is not yet a deployed,
   externally-audited product.
10. **Managed access (P9) is a mechanism, not an authority.** The plane enforces tiers and binds the legitimacy
    evidence tamper-evidently, but it verifies legitimacy through a pluggable hook; the credentialing authority is an
    integration point the deployment must supply. It is not a deployed access-control regime.
11. **The two strengtheners are documented nulls.** Neyman-Pearson conformal selection adds calibrated control
    but not power at matched alpha (the certified bound stands); confidence-gated structural fusion does not lift
    the 1%-FPR operating point because the held-out structures are already high-confidence (the failure is
    fold-distance, not low pLDDT). Neither is shipped as a claim. A full-trajectory monitor and a scaled red-team are
    a post-v1.0 fast-follow.

## 5. Scope/limit statement for every headline claim

| Headline claim | What it rests on | Scope / limit |
|---|---|---|
| **C - no LLM screens a cargo sequence** | ESM2 head TPR@1%FPR 0.72 vs open LLMs 0.00-0.60@49%FPR (n=200) | Model/date-specific (2026-06); the cargo gate is conceded non-novel at the component level; margin over composition is modest at 1% FPR |
| **D - open LLM judges are jailbroken; firewall is not** | Prompt-injection flips 50-83% on open models; firewall 0% by construction | Tested models/date-specific; a stronger future model could shift it; firewall immunity is architectural (reads structured plan) |
| **Certified false-refuse ceiling** | Clopper-Pearson 0/288 -> <=0.0103, alpha in {.01,.05,.10} | Bounds **over-refusal only**; says nothing about hazard-catch |
| **Locus interception 80-82% (two censuses)** | Concordance with COSMIC/OncoKB independent labels | Concordance-with-curation, **not** prevented harm; misses ~20% of COSMIC |
| **Locus outcome-validated (mouse)** | CCGD held-out AUROC 0.605 / OR 3.34, non-circular | Modest effect; mouse + gene-level; positional/human/wet-lab pending |
| **De-novo fusion recall 0.909 (kinase 1.0)** | 471 off-list COSMIC fusion pairs, 0% benign FP | Recall partly role-driven; FP control is non-cancer pairs |
| **Decomposition 100% catch / 0% FP** | Two modeled evasion families | Necessary-not-sufficient; novel obfuscation can evade |
| **Positional catches 10,834 gene-body misses** | VISDB coverage count | A count, not a calibrated/validated rate |
| **Monotone combiner** | 5,000-case perturbation proof | A property of the combiner, not a guarantee about the world |
| **Managed access (P9) completes the NTI guardrail set** | Deterministic (verdict x tier) matrix; tier bound into the passport + audit | A built mechanism, not a deployed credentialing authority (an integration point) |
| **Graded taxonomy + partial content gate** | Deterministic map from axis verdicts; regex content gate with negative controls | A deterministic content tier, not a learned judgment; ambiguous axes collapse to review |
| **NP conformal selection** | Controls false-escalation at alpha on the firewall corpus | Documented null: calibrated control, NOT higher power at matched alpha; the certified bound stands |
| **Confidence-gated structural fusion** | pLDDT-gated re-run on the <=40%-id holdout | Documented null: no 1%-FPR lift (high-pLDDT structures; failure is fold-distance); AUROC corroborator only |

## 6. Responsible use

Defensive screen, **safe proxies only**, **no evasion cookbook**, **artifact-decides-not-framing**. Signatures are
function/family/taxon-level (public Pfam + control-list references) - no hazard sequences are shipped or required.
BioFirewall is **not** a substitute for institutional biosafety review, IBC approval, or synthesis-stage screening;
it is an additional, auditable layer that makes a capable design AI safer to operate.

---

*This system card is versioned with the package. Every claim above maps to a pre-registered, frozen result in
`prereg/ws_biofirewall.yaml` and a benchmark in `docs/BENCHMARK.md`. Limitations are carried verbatim from the
prereg and README; nothing here is softened relative to those.*
