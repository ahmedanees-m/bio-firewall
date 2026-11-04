# BioFirewall - Reproduction Guide

Reproducing a single-maintainer result is what makes it credible. This guide lets a stranger regenerate every
reported number on a clean machine, separating what reproduces **from the committed repo alone** (open data) from
what needs the **local-only** data (COSMIC/OncoKB/VISDB/controlled-access - never committed).

## 0. Clean environment

```bash
git clone https://github.com/ahmedanees-m/bio-firewall && cd bio-firewall
python -m venv .venv && . .venv/bin/activate     # Python 3.11 or 3.12
make install                                      # pip install -e ".[dev]"  (pulls pen-stack>=0.2.0,<0.3.0)
```
> If your machine only has `python3` (no `python`), pass `PY=python3` to every `make` target.

**Container alternative (pinned Python 3.11, no host Python setup).** The image is self-contained and reproduces the
committed-data numbers with one command. Pull the published image for the exact environment the release was verified
in, or build it yourself from the same Dockerfile:

```bash
docker run --rm ghcr.io/ahmedanees-m/bio-firewall:0.2.0 make reproduce   # published image, nothing to build

make docker-build        # docker build -t biofirewall .   (base image: python:3.11-slim)
make docker-reproduce    # runs `make reproduce` inside the image you just built
```
The published image is built from the tagged tree by `.github/workflows/release-image.yml`, which smoke-tests
`screen()` and the signed hazard KB at build time and re-verifies the pushed image before the job succeeds.

**pen-stack compatibility.** The dependency is bounded `>=0.2.0,<0.3.0`, capped below the next minor; the suite is verified green against the pinned pen-stack release.
The suite is 217 tests. Two can skip for environment reasons: the local-only COSMIC oracle, and the reconcile end-to-end
test, which drives pen-stack's real `safety_gate` and needs a pen-stack source **checkout** (`export PEN_STACK_HOME=/path/to/pen-stack`)
because the pip wheel ships the library, not `configs/safety/policy.yaml`. Where pen-stack resolves to a source checkout the
reconcile test runs and the result is **216 passed / 1 skipped**, the single skip being the COSMIC oracle. The reconcile
adapter's decision logic is fully covered by mocked-gate unit tests regardless.

## 1. Reproduce from the committed repo (open data only)

```bash
make lint        # ruff - clean
make test        # the full suite (217 tests) - validates every committed metric/logic path
make reproduce   # B7 monotone-combiner proof + B5 session monitor (120/120) + the suite above
make prereg-sha  # SHA-256 of the SHA-locked frozen analysis specification (must match the value in the release notes)
```
A clean run reports lint clean; the suite green with at most two environment skips (the local-only COSMIC oracle
and the reconcile end-to-end, which needs a pen-stack checkout as above); `B7 monotone combiner: PASS (reps=5000)`;
and `B5 session monitor (decomposition): 120/120 caught on the families whose attacks evade the per-call screen`.

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

| Benchmark | Reference value (seed 1234, within tolerance) |
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
