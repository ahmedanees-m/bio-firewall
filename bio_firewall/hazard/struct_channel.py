"""WS-STRUCT (v0.6.0) - a structural remote-homology channel + a 3-signal ensemble for the cargo axis.

AI homologs that evade SEQUENCE similarity often retain FOLD. So we add a structure-based signal: predict/fetch a
candidate's structure (AlphaFold-DB; ESMFold when GPU is free) and Foldseek-search it against a reference of hazard
FOLDS (public folds only - no hazard sequences shipped). Being a fold signal, it is COMPOSITION-INDEPENDENT, so it
also backstops WS-CARGO-DECORR (the cleanest refutation of the composition confound).

The cargo screen then fuses THREE orthogonal signals and ABSTAINS on disagreement (routes to human):
  - sequence-profile / homology (the Benchmark-2 baseline),
  - ESM embedding (the function-aware head),
  - structure (this channel).

This module holds the fusion + abstention MATH (testable, no torch/Foldseek). The Foldseek run + AlphaFold-DB fetch
are in `eval/cargo_bench/struct_bench.py` (need the tools + the local proxies)."""
from __future__ import annotations


def normalize01(xs):
    import numpy as np
    x = np.asarray(xs, float)
    lo, hi = np.nanmin(x), np.nanmax(x)
    return (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)


def ensemble_score(esm, struct, homology=None):
    """Mean of the available normalized signals - each a per-candidate toxin-likeness in [0,1]."""
    import numpy as np
    sigs = [normalize01(esm), normalize01(struct)]
    if homology is not None:
        sigs.append(normalize01(homology))
    return np.mean(np.vstack(sigs), axis=0)


def confidence_gated_score(esm, struct, plddt, plddt_min: float = 70.0):
    """WS-STRUCT-GATED (v0.8.0): the v0.6 MEAN ensemble failed at 1%-FPR because a weak, low-confidence fold channel
    diluted ESM. Gate the fold signal on STRUCTURE CONFIDENCE: fuse esm+struct ONLY where the predicted-structure
    pLDDT >= plddt_min; everywhere else defer to ESM alone. By construction the gated score equals ESM wherever the
    structure is not trusted, so it cannot dilute ESM at the operating point."""
    import numpy as np
    e = normalize01(esm)
    s = normalize01(struct)
    plddt = np.asarray(plddt, float)
    hi = plddt >= plddt_min
    out = e.copy()
    out[hi] = 0.5 * (e[hi] + s[hi])                  # fuse only where the fold channel is confident
    return out


def abstain_mask(esm, struct, lo: float = 0.35, hi: float = 0.65):
    """Abstain (route to human) when the two channels STRONGLY DISAGREE: one calls toxin (>hi) while the other
    calls benign (<lo). Disagreement is exactly where a single-signal screen is least trustworthy."""
    e, s = normalize01(esm), normalize01(struct)
    return ((e > hi) & (s < lo)) | ((s > hi) & (e < lo))


def tpr_at_fpr(y, p, fpr_target: float = 0.01):
    import numpy as np
    y, p = np.asarray(y, int), np.asarray(p, float)
    neg = np.sort(p[y == 0])
    if not len(neg):
        return float("nan")
    thr = neg[max(0, int(np.ceil((1 - fpr_target) * len(neg))) - 1)]
    return float(((p >= thr) & (y == 1)).sum() / max(1, (y == 1).sum()))
