"""Function-aware cargo screen (the ToxDL / OmniTox direction): an ESM2 embedding scored by nearest-centroid
(toxin vs benign). It catches low-identity homologs that EVADE signature/homology screens, because the ESM
embedding captures protein FUNCTION beyond sequence identity.

OPTIONAL + graceful: it needs `fair-esm` + torch (the `ml` extra) for live embedding, and the vendored centroids
(`vendored_data/cargo_centroids.npz`, derived from PUBLIC toxin/benign reference proteins — only the centroid
VECTORS ship, never sequences). When ESM/centroids are unavailable the caller falls back to the Guardian screen.

HONESTY: this is a probabilistic signal -> it routes to REVIEW (scope_flag), not an auto-block; the prereg gate is a
homology-clustered <=40%-identity evaluation (TPR@1%FPR + shortcut probes), declared in prereg/ws_biofirewall.yaml."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_VD = Path(__file__).resolve().parents[2] / "vendored_data"   # bio_firewall/hazard/ -> repo root
TOXIN_LEAN_THRESHOLD = 0.02          # score > this => toxin-leaning -> flag for review


@lru_cache(maxsize=1)
def _centroids():
    p = _VD / "cargo_centroids.npz"
    if not p.exists():
        return None
    import numpy as np
    d = np.load(p)
    return {"tox": d["tox_centroid"], "ben": d["ben_centroid"]}


@lru_cache(maxsize=1)
def _model():
    try:
        import esm
        import torch
        m, a = esm.pretrained.esm2_t6_8M_UR50D()
        m.eval()
        return m, a, torch
    except Exception:  # noqa: BLE001 - ml extra absent -> function-aware screen unavailable
        return None


def _embed(sequence: str):
    got = _model()
    if got is None:
        return None
    m, a, torch = got
    seq = sequence[:1022]
    _, _, toks = a.get_batch_converter()([("q", seq)])
    with torch.no_grad():
        rep = m(toks, repr_layers=[6])["representations"][6]
    return rep[0, 1:len(seq) + 1].mean(0).numpy()


def score_embedding(emb) -> float | None:
    """Toxin-lean score from a precomputed embedding: cos(emb, toxin_centroid) - cos(emb, benign_centroid).
    >0 = toxin-leaning. (Testable without running ESM — used with stored reference embeddings.)"""
    c = _centroids()
    if c is None or emb is None:
        return None
    import numpy as np
    def cos(x, y):
        return float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-9))
    return cos(emb, c["tox"]) - cos(emb, c["ben"])


def function_aware_score(sequence: str | None) -> tuple[float | None, bool]:
    """(score, available). available=False if ESM/centroids unavailable -> caller uses the Guardian signature screen."""
    if not sequence or _centroids() is None:
        return None, False
    emb = _embed(sequence)
    if emb is None:
        return None, False
    return score_embedding(emb), True
