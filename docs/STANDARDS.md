# Standards Alignment

BioFirewall is a design-stage governance layer. This note records how the artifact aligns with the conventions the
field is standardizing on, so the benchmark and the living knowledge base are interoperable rather than bespoke. Where
a standard is not yet public, the alignment is stated as intent plus an explicit schema hook; no conformance is
claimed. All references were independently verified (see `DATA_ID_VERIFICATION_v0.8.md`).

## 1. NIST baseline-screening dataset conventions

The safe-proxy locus benchmark exports in a shape that mirrors the NIST baseline-screening test set:

- Reference: NIST, "test dataset for assessing baseline nucleic acid sequence screening", persistent id
  `ark:/88434/mds2-3787` (published 2025-05-21); Laird et al., "Inter-tool analysis of a NIST dataset for assessing
  baseline nucleic acid sequence screening", bioRxiv `10.1101/2025.05.30.655379` (2025).
- Export: `bio_firewall.standards.export_benchmark()` emits blinded record ids (`BF-#####`) plus a separate answer
  key, mirroring the NIST convention of blinded headers with labels supplied separately, a declared field schema, and
  a content checksum. The committed artifact is `standards/nist_benchmark_export.json`; regenerate with
  `python tools/export_nist_benchmark.py`; validate with `bio_firewall.standards.validate_export()`.
- Scope statement: this is a design-stage analog. The records are public gene-symbol proxies (Tier-1 clinical-CIS
  loci versus benign therapeutic and safe-harbour loci), not sequences and not hazards. BioFirewall screens
  design-stage plans; it is complementary to, not a replacement for, the synthesis-stage sequence screening the NIST
  dataset targets. The alignment is to the dataset conventions, not a claim to be a synthesis screener.

## 2. IBBIS DNA Screening Standards Consortium (DSSC)

The living hazard knowledge base is described against the IBBIS DNA Screening Standards Consortium (launched
2025-11-06) and its Common Mechanism lineage:

- Aligned today: per-entry hazard `type` (a function- or sequence-of-concern category, in the Common-Mechanism
  style), per-entry `provenance` and citation, a versioned release (`kb_version` / `released` / `schema_version`),
  and an integrity digest plus signed release (`content_sha256` / `hmac_sha256`, tamper-evident).
- Hooks pending the published standard: a mapping from the benchmark record ids to a DSSC validated-test-set id when
  the consortium publishes one, and a crosswalk from BioFirewall hazard `type` values to the DSSC sequence-of-concern
  taxonomy once it is finalized.
- No conformance is claimed; this is alignment intent plus the documented hooks. See
  `bio_firewall.standards.kb_standards_alignment()`.

## 3. OSTP interagency window

The 2024 Framework for Nucleic Acid Synthesis Screening (OSTP, 2024-04-29, Section 4.4(b)(i)) provides for a US
interagency state-of-the-art assessment of nucleic-acid-synthesis screening before 2026-10-13. BioFirewall's position
for that window:

- Design-stage governance (screening genome-writing plans before synthesis, with a signed passport) is complementary
  to synthesis-stage sequence screening (Wittmann et al., Science 2025, `10.1126/science.adu8578`). The two layers
  compose; design-stage governance is not a replacement for, nor an implementation of, the synthesis-screening
  framework.
- Caveat: the 2024 Framework may be revised or replaced under the 2025-05-05 Executive Order, "Improving the Safety
  and Security of Biological Research." This note aligns with a moving target; the structured form is
  `bio_firewall.standards.OSTP_NOTE`.

## Residual posture

Standards alignment tracks a moving target. Where the IBBIS DSSC standards are still forming and where the OSTP
framework may change, the artifact ships alignment intent plus schema hooks and makes no conformance claim. The safe
proxies that bound every screening claim are a test, evaluation, validation, and verification necessity, not real
hazards.
