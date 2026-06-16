# BioFirewall — Data Licenses

**The rule:** the `bio-firewall` repo vendors **open data only** (CC0 / CC-BY / public-domain). License-restricted
sources (OncoKB, COSMIC) are **never committed, never training data** — they are optional, local-only enrichers a
registered user pulls under their own license (`tools/fetch_licensed_sources.py`, Phase 1), for validation only.

| Source | Provides | License | Train ML? | Redistribute? |
|---|---|---|---|---|
| **CancerMine** (10.1038/s41592-019-0422-y; Zenodo 7689627) | oncogene / TSG / driver list | **CC0** | ✅ | ✅ |
| **DepMap** (CRISPRGeneEffect) | essential genes | CC BY 4.0 | ✅ | ✅ (attrib) |
| **gnomAD** (pLI / LOEUF) | dosage / constraint | open | ✅ | ✅ |
| **ClinVar / ClinGen** | dosage sensitivity | public domain | ✅ | ✅ |
| **GENCODE / Ensembl** | gene coordinates | open | ✅ | ✅ |
| **Pfam / InterPro** | function families | open | ✅ | ✅ |
| **Select-Agent / Australia-Group** | controlled-agent taxa | public (regulatory) | ✅ | ✅ |
| public toxin/benign protein sets | cargo function-aware ML training | open | ✅ | ✅ |

### Restricted — NOT shipped (local-only, your own license, validation-only)
- **OncoKB** — no ML training, no redistribution; benchmarking with written permission only.
- **COSMIC CGC** — free w/ registration, no redistribution; citations of methodology are fine.

### Vendored artifacts (committed, CC0/open)
- `vendored_data/locus_genes.parquet` — 4,695 genes (CancerMine oncogene/TSG/driver + DepMap essential, with
  GENCODE coords), derived from PEN-STACK **v6.6.0** (the license-clean, CancerMine-sourced build — *not* any v6.5
  COSMIC-derived copy). Powers the locus axis.
- `vendored_data/gnomad_constraint.parquet` — 19,197 genes with pLI/LOEUF (gnomAD constraint, open aggregate data).
  Dosage-sensitivity / haploinsufficiency signal for the locus axis.
- `vendored_data/oncogenic_fusions.yaml` — curated open set of canonical oncogenic gene fusions (literature facts,
  not a restricted DB). Edit-type axis.
- `vendored_data/cargo_centroids.npz` — ESM2 centroid VECTORS for the function-aware cargo classifier, built from
  PUBLIC toxin/benign reference proteins (only the float centroids ship — never sequences). Apache-2.0/derived.
- `vendored_data/genotoxicity_oracle.yaml` — the CancerMine-sourced genotoxicity oracle (PEN-STACK v6.6.0).

A CI test (`tests/test_data_licenses.py`) fails if a non-permissive source appears in the vendored data or a raw
restricted gene-list is committed.
The legal crux: copyright protects the *compiled database*, not the *fact* that a gene is an oncogene — so the gene
*list* is sourced from a **CC0 compilation (CancerMine)**.
