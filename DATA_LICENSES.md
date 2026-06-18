# BioFirewall - Data Licenses

**The rule:** the `bio-firewall` repo vendors **open data only** (CC0 / CC-BY / public-domain). License-restricted
sources (OncoKB, COSMIC) are **never committed, never training data** - they are optional, local-only enrichers a
registered user pulls under their own license (`tools/fetch_licensed_sources.py`, Phase 1), for validation only.

| Source | Provides | License | Train ML? | Redistribute? |
|---|---|---|---|---|
| **CancerMine** (10.1038/s41592-019-0422-y; Zenodo 7689627) | oncogene / TSG / driver list | **CC0** | yes | yes |
| **DepMap** (CRISPRGeneEffect) | essential genes | CC BY 4.0 | yes | yes (attrib) |
| **gnomAD** (pLI / LOEUF) | dosage / constraint | open | yes | yes |
| **ClinVar / ClinGen** | dosage sensitivity | public domain | yes | yes |
| **GENCODE / Ensembl** | gene coordinates | open | yes | yes |
| **Pfam / InterPro** | function families | open | yes | yes |
| **Select-Agent / Australia-Group** | controlled-agent taxa | public (regulatory) | yes | yes |
| public toxin/benign protein sets | cargo function-aware ML training | open | yes | yes |

### Restricted - NOT shipped (local-only, your own license, validation-only)
- **OncoKB** - no ML training, no redistribution; benchmarking with written permission only.
- **COSMIC CGC** - free w/ registration, no redistribution; citations of methodology are fine.

### Vendored artifacts (committed, CC0/open)
- `vendored_data/locus_genes.parquet` - 4,695 genes (CancerMine oncogene/TSG/driver + DepMap essential, with
  GENCODE coords), derived from PEN-STACK **v6.6.0** (the license-clean, CancerMine-sourced build - *not* any v6.5
  COSMIC-derived copy). Powers the locus axis.
- `vendored_data/gnomad_constraint.parquet` - 19,197 genes with pLI/LOEUF (gnomAD constraint, open aggregate data).
  Dosage-sensitivity / haploinsufficiency signal for the locus axis.
- `vendored_data/oncogenic_fusions.yaml` - curated open set of canonical oncogenic gene fusions (literature facts,
  not a restricted DB). Edit-type axis.
- `vendored_data/cargo_centroids.npz` - ESM2 centroid VECTORS for the function-aware cargo classifier, built from
  PUBLIC toxin/benign reference proteins (only the float centroids ship - never sequences). Apache-2.0/derived.
- `vendored_data/genotoxicity_oracle.yaml` - the CancerMine-sourced genotoxicity oracle (PEN-STACK v6.6.0).

A CI test (`tests/test_data_licenses.py`) fails if a non-permissive source appears in the vendored data or a raw
restricted gene-list is committed.
The legal crux: copyright protects the *compiled database*, not the *fact* that a gene is an oncogene - so the gene
*list* is sourced from a **CC0 compilation (CancerMine)**.

### Pinned data releases (for reproduction - `make reproduce-local`)

Every benchmark number is regenerable from these exact releases; pinning them is what makes the artifact
reproducible by a stranger (WS-REPRO).

| Source | Pinned release | Used by |
|---|---|---|
| CancerMine | Zenodo record **7689627** (CC0), as built into PEN-STACK v6.6.0 | locus axis, edit-mech, locus-pos |
| gnomAD constraint | **v2.1.1** LoF-metrics (pLI/LOEUF) | locus dosage axis |
| GENCODE | **v46** (GRCh38) basic gene coords | locus-pos (oncogene TSS), VISDB site->gene mapping |
| COSMIC Cancer Gene Census | **v104** (GRCh38) - *local-only*, never committed | benchmark labels (B1), edit-mech held-out (B8) |
| OncoKB Cancer Gene List | retrieved release - *local-only*, never committed | benchmark second oracle (B1b) |
| VISDB | **v1.0** per-virus hg38 catalogues - *local-only* | locus-outcome floor (B6), locus-pos coverage (B9) |
| AlphaFold-DB | **v6** monomer models (`AF-{ACC}-F1-model_v6.cif`) | structural channel (B10) |
| UniProt toxins/benign | KW-0800 reviewed vs reviewed non-toxin, length 50-500 (frozen FASTA, seed 1234) | cargo gate (B2), decorr (B2b), struct (B10) |
| Foldseek / MMseqs2 | `ghcr.io/steineggerlab/foldseek:latest`; MMseqs2 easy-cluster `--min-seq-id 0.4` | B10 / B2 |

Seeds are frozen (**1234**) throughout. The frozen result values are SHA-locked in `prereg/ws_biofirewall.yaml`.
