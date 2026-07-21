# BioFirewall - Hazard Knowledge Base (living, versioned, signed)

Hazard screening only stays useful if its signatures are **maintained** as new threats are characterized - the
antivirus model. BioFirewall therefore keeps its hazard signatures in a **versioned, provenanced, signed**
knowledge base rather than a frozen blob. Releases live in `bio_firewall/vendored_data/hazard_kb/<version>.yaml`; the loader is
`bio_firewall.kb`.

## What's in it

Function/family/taxon-level signatures only - **no hazard sequences** (consistent with the defensive posture):

| `type` | meaning | current source |
|---|---|---|
| `genotoxic_cis_locus` | clinical insertional-oncogenesis loci | gene-therapy adverse-event literature (DOIs) |
| `oncogenic_fusion_pair` | canonical driver fusions (gene pair) | literature-curated open set |
| `fusion_kinase` | recurrent fusion kinases (constitutive-activation mechanism) | public cancer-fusion biology |
| `ig_tcr_locus` | immunoglobulin / TCR super-enhancer loci | public |
| `select_agent_toxin` | listed select-agent and Australia-Group toxins (names only) | 42 CFR 73 / 7 CFR 331 / 9 CFR 121; Australia Group control list |
| `select_agent_toxin_organism` | source organisms of listed toxins (screened only together with a toxin descriptor, i.e. an indirect naming) | same control lists |

## Entry schema

```yaml
- id: CIS-LMO2                      # stable unique id
  type: genotoxic_cis_locus        # one of the types above
  value: LMO2                      # gene symbol, [gene, gene] pair, or locus
  provenance:                      # REQUIRED - every signature carries its source
    source: "SCID-X1 gammaretroviral trials - T-ALL"
    doi: "10.1126/science.1088547"
  added_in: "0.3.0"                # the package version the signature entered
```

## Integrity & signing

Each release carries:
- `content_sha256` - a **keyless** digest over the canonical content (anyone reproduces it; CI verifies it);
- `hmac_sha256` - an HMAC over the same content (tamper-evident **signature**). The public release uses a public
  integrity key; a maintainer signs production releases with a private key. A single edited entry breaks both.

Verify: `python -c "from bio_firewall.kb import load_kb, verify_kb; print(verify_kb(load_kb()))"`.

## Release cadence & contribution path

- **Cadence:** a KB minor release accompanies each package minor release that adds/changes signatures; out-of-band
  patch releases may add urgent signatures.
- **Contribute:** open a PR that (1) adds the entry to `tools/build_hazard_kb.py` with **provenance** (a public DOI
  / control-list reference - never a hazard sequence), (2) bumps the KB version, (3) regenerates the release
  (`python tools/build_hazard_kb.py <version> <date>`), (4) keeps the consistency + signature test green
  (`tests/test_kb.py`). Provenance is mandatory; an entry without a citable, public, function/family-level source is
  rejected.
- **Consistency gate:** the KB must be a **superset** of the signatures the code screens on - the CI test fails if a
  signature is in the code but missing from the signed KB (so the KB cannot silently drift from the screen).
