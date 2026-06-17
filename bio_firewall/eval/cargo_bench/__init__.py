"""Benchmark 2 — cargo function-aware ML, the pre-registered gate (prereg/ws_biofirewall.yaml::axis1_function_aware_ml).

The honest question: can an ESM2 embedding + a trained head catch a toxin homolog that a homology/BLAST screen
MISSES because the test protein has no >40%-identity neighbour in the training set (the "never-before-seen AI
homolog")? We answer it with a homology-clustered held-out evaluation:

  1. public UniProt toxins (KW-0800, reviewed) vs benign (reviewed non-toxin, length-matched) — SAFE PROXIES
  2. MMseqs2 easy-cluster @40% identity -> hold out WHOLE clusters (no test protein has a >40%-id train neighbour)
  3. ESM2-650M mean-pooled embeddings (SHIP VECTORS ONLY, never sequences)
  4. trained head (logistic regression) vs homology baseline (mmseqs search test->train-toxins by %identity)
  5. TPR@1%FPR (the deployment operating point), FPR@95%TPR, AUROC, AUPRC + cluster-bootstrap CIs
  6. shortcut probes (length / amino-acid composition): does the signal survive controls -> is it FUNCTIONAL?

GATE (pre-registered): the ESM head beats homology B0 at TPR@1%FPR on the <=40% held-out clusters, CI excluding
the baseline; shortcut probes do not explain the signal.

Requires `mmseqs` on PATH + the `ml` extra (fair-esm + torch). Runs on CPU; a GPU helps. Entry point: `run.run()`.
"""
from .run import run

__all__ = ["run"]
