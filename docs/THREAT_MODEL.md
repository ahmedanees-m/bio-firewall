# BioFirewall - Threat Model

Authoritative source: `../../Final_Part_v3.0/Biofirewall/BIOFIREWALL_BLUEPRINT_v0.4_FINAL.md` Section 0, Section 8.

**The gap (Layer B).** Three places to put a biosafety control; the field built two - model-level (chatbot
classifiers) and the synthesis chokepoint (Common Mechanism / SecureDNA). The **design / planning stage is empty.**
ABC-Bench (ICML 2026) shows frontier agents already design assemblable DNA *and* evade synthesis screening, so
Layer B must read the artifact **in-workflow**, where the agent cannot route around it.

**Adversary.** A capable design AI (or a user driving one) producing a genome-writing plan that is individually
plausible and may evade homology-based sequence screening - AI homologs at low identity, combinatorial/split
hazards, or hazards that live in *where/how/inheritance/scale* rather than in the inserted sequence.

**What BioFirewall defends.** The five genome-writing-native axes - especially the four (locus, edit, germline,
scale) a protein/sequence screener structurally cannot see. A safeguard, not a guarantee: screening reduces, not
eliminates; "necessary, not sufficient."

**Robustness (P6).** Framing-stripped - the artifact decides, not the cover story; reframing / prompt-injection
must not flip `refuse -> allow`; no-fabrication holds under the red-team harness. Safe proxies only (TEVV).
