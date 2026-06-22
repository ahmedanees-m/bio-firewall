# BioFirewall - Threat Model

Authoritative source: `../../Final_Part_v3.0/Biofirewall/BIOFIREWALL_BLUEPRINT_v0.4_FINAL.md` Section 0, Section 8.

**The gap (Layer B).** Three places to put a biosafety control; the field built two - model-level (chatbot
classifiers) and the synthesis chokepoint (Common Mechanism / SecureDNA). The **design / planning stage is empty.**
ABC-Bench (NeurIPS 2025 BioSafe GenAI workshop; arXiv:2606.11150) shows frontier agents already design assemblable
DNA *and* evade synthesis screening, so Layer B must read the artifact **in-workflow**, where the agent cannot route
around it.

**The expanded surface (PEN-STACK v7.0).** PEN-STACK 7.0 completed its A->J genome-writing pipeline, adding a typed,
ontology-backed intent layer (Stage A, the SBOL3 `WriteRequest`) and - for the first time - a design->physical
-execution bridge (Stage J, the cloud-lab connector; mock/dry-run today, but the path now exists). PEN-STACK's own
architecture designates BioFirewall as **Stage K - the comprehensive downstream screen** that completes the A->K
pipeline. BioFirewall consumes the typed intent directly (`adapters/writespec.py`), gates the execution bridge so no
submission proceeds without a verified `allow` passport (`adapters/cloudlab_gate.py`), and reconciles its verdict with
PEN-STACK's in-design `safety_gate` as a conservative meet (`adapters/reconcile.py`). PEN-STACK's in-design gate is
necessary-not-sufficient; BioFirewall is the comprehensive screen. Design platforms coupling directly to automated
laboratories collapse the design->execution gap, which is exactly why an in-workflow design-stage screen is necessary
rather than optional. (PEN-STACK 7.0 also adds generative stages - writer-enzyme and capsid design; screening of
generated sequences flows through the existing cargo/delivery axes and is a named ongoing surface.)

**Adversary.** A capable design AI (or a user driving one) producing a genome-writing plan that is individually
plausible and may evade homology-based sequence screening - AI homologs at low identity, combinatorial/split
hazards, or hazards that live in *where/how/inheritance/scale* rather than in the inserted sequence.

**What BioFirewall defends.** The five genome-writing-native axes - especially the four (locus, edit, germline,
scale) a protein/sequence screener structurally cannot see. A safeguard, not a guarantee: screening reduces, not
eliminates; "necessary, not sufficient."

**Robustness (P6).** Framing-stripped - the artifact decides, not the cover story; reframing / prompt-injection
must not flip `refuse -> allow`; no-fabrication holds under the red-team harness. Safe proxies only (TEVV).
