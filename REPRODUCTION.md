# BioFirewall - Reproduction Guide

Reproducing a single-maintainer result is what makes it credible. This guide lets a stranger regenerate every
headline number on a clean machine, separating what reproduces **from the committed repo alone** (open data) from
what needs the **local-only** data (COSMIC/OncoKB/VISDB/controlled-access - never committed).

## 0. Clean environment

```bash
git clone https://github.com/ahmedanees-m/bio-firewall && cd bio-firewall
python -m venv .venv && . .venv/bin/activate     # Python 3.11 or 3.12
make install                                      # pip install -e ".[dev]"  (pulls pen-stack>=0.1.0,<0.2.0)
```
> If your machine only has `python3` (no `python`), pass `PY=python3` to every `make` target.

**Container alternative (pinned Python 3.11, no host Python setup).** The image is self-contained and reproduces the
committed-data numbers with one command. Pull the published image for the exact environment the release was verified
in, or build it yourself from the same Dockerfile:

```bash
docker run --rm ghcr.io/ahmedanees-m/bio-firewall:0.1.0 make reproduce   # published image, nothing to build

make docker-build        # docker build -t biofirewall .   (base image: python:3.11-slim)
make docker-reproduce    # runs `make reproduce` inside the image you just built
```
The published image is built from the tagged tree by `.github/workflows/release-image.yml`, which smoke-tests
`screen()` and the signed hazard KB at build time and re-verifies the pushed image before the job succeeds.

**pen-stack compatibility.** The dependency is bounded `>=0.1.0,<0.2.0`; the suite is verified green against the pinned pen-stack release.
Verified on a clean `pip install`: 165 passed / 2 skipped. The 2 skips are the local-only COSMIC oracle and the reconcile end-to-end test: the latter
drives pen-stack's real `safety_gate`, which needs a pen-stack source **checkout** (`export PEN_STACK_HOME=/path/to/pen-stack`)
because the pip wheel ships the library, not `configs/safety/policy.yaml`. With that checkout the reconcile test runs
and the count is **166 passed / 1 skipped**. The reconcile adapter's decision logic is fully covered by mocked-gate
unit tests regardless.

## 1. Reproduce from the committed repo (open data only)

```bash
make lint        # ruff - clean
make test        # the full suite (167 tests) - validates every committed metric/logic path
make reproduce   # the monotone-combiner monotonicity proof (B7 PASS) + the suite above
make prereg-sha  # SHA-256 of the SHA-locked pre-registration (must match the value in the release notes)
```
Expected on a clean `pip install`: lint clean; **165 passed** (2 skipped: the local-only COSMIC oracle and the
reconcile end-to-end, which needs a pen-stack checkout as above); `B7 monotone combiner: PASS (reps=5000)`. The test suite *is* the proof that
the cargo/conformal/decomposition/edit-mech/locus-pos/struct **math** matches the frozen results.

## 2. Reproduce the data-dependent benchmarks (local-only data)

These need the pinned data (see [DATA_LICENSES.md](DATA_LICENSES.md) -> "Pinned data releases"), obtained under your
own licence and **kept local**:

```bash
export PEN_STACK_HOME=/path/to/pen-stack
export PEN_STACK_SAFETY_AUDIT=/tmp/bf_audit.log        # writable path for the Guardian audit
export BF_BENCH_ORACLES=/path/to/bench_oracles          # cosmic_cgc_v104.tsv (+ oncokb) - NEVER committed
export BF_B2_DIR=/path/to/bf_b2                          # frozen Benchmark-2 vectors + public-proxy fastas
export BF_VISDB_DIR=/path/to/visdb  BF_GENE_COORDS=/path/to/gene_coords.parquet
make reproduce-local                                    # B1/B3/B4/B4b/B6/B8/B9
```

| Benchmark | Expected (seed 1234, within tolerance) |
|---|---|
| B1 locus interception (COSMIC) | 80.4% (CI .78-.83) ; Tier-1 12/12 |
| B2 cargo gate | ESM TPR@1%FPR 0.72 vs homology 0.207 |
| B2b decorr | AUROC: DANN 0.985 vs composition 0.93 (paired +0.054, excl. 0) |
| B4b conformal | false-refuse cert <=0.0103 ; confidence monotone 1.00 > 0.69 > 0.10 |
| B5 decomposition | catch 100% (CI [1,1]) / 0% FP on the two evasion families |
| B6 locus-outcome (VISDB) | AUROC 0.449 / OR 0.577 (access-gated negative result) |
| B8 de-novo fusion | recall 0.909 (kinase 1.00) / benign FP 0.0 |
| B9 positional coverage | 10,834 / 17,158 flags not in an oncogene body |
| B10 structural | incremental TPR@1%FPR -0.48 (negative result) ; structure AUROC 0.882 |

The control-vs-advisor **panel** (C + D) reproduces from one command - see [docs/PANEL.md](docs/PANEL.md).

## 3. Verify the signed hazard KB

```bash
python -c "from bio_firewall.kb import load_kb, verify_kb; print(verify_kb(load_kb()))"   # True
```

## 4. Remaining external steps (NOT something the maintainer can self-certify)

- **Independent reproduction.** One person other than the author should run Section 1 (and Section 2 if they hold the
  licensed data) on a clean image and confirm the numbers within tolerance; record the confirmation + any deltas
  here. *This is the step that converts "the author says it reproduces" into "it reproduces."* - **pending an
  external runner.**
- **Zenodo DOI.** Mint by connecting this GitHub repo to Zenodo and publishing a tagged release; the
  deposit metadata is in `.zenodo.json` and `CITATION.cff`. The restricted/local-only data is **not** part of the
  deposit. - **pending the author's Zenodo account.**
