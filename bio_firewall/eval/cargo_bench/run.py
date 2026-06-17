"""Benchmark 2 pipeline. See package docstring. Needs `mmseqs` on PATH + `fair-esm`+`torch` (the `ml` extra).

Reproduce on a machine with mmseqs + torch:
    python -c "from bio_firewall.eval.cargo_bench import run; run(out_dir='bench_cargo')"

Env: BF_B2_N (per-class cap, default 1200), BF_B2_ESM (default esm2_t33_650M_UR50D), TORCH_HOME (weight cache)."""
from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

SEED = 1234
AAS = "ACDEFGHIKLMNPQRSTVWY"


def _fetch_fasta(query: str, path: Path) -> None:
    qs = urllib.parse.urlencode({"query": query, "format": "fasta", "includeIsoform": "false"})
    req = urllib.request.Request(f"https://rest.uniprot.org/uniprotkb/stream?{qs}",
                                 headers={"User-Agent": "bio-firewall-bench/1.0"})
    path.write_bytes(urllib.request.urlopen(req, timeout=300).read())


def _parse_fasta(path: Path) -> dict[str, str]:
    """UniProt sp|ACC|NAME -> {ACC: sequence} (ACC matches the IDs MMseqs2 emits)."""
    seqs: dict[str, str] = {}
    name, buf = None, []
    for line in path.read_text().splitlines():
        if line.startswith(">"):
            if name:
                seqs[name] = "".join(buf)
            hdr = line[1:].split()[0].split("|")
            name = hdr[1] if len(hdr) >= 3 else line[1:].split()[0]
            buf = []
        else:
            buf.append(line.strip())
    if name:
        seqs[name] = "".join(buf)
    return seqs


def _tpr_at_fpr(y, p, fpr_target=0.01):
    import numpy as np
    neg = np.sort(p[y == 0])
    if not len(neg):
        return float("nan")
    thr = neg[max(0, int(np.ceil((1 - fpr_target) * len(neg))) - 1)]
    return float(((p >= thr) & (y == 1)).sum() / max(1, (y == 1).sum()))


def _fpr_at_tpr(y, p, tpr_target=0.95):
    import numpy as np
    pos = np.sort(p[y == 1])
    if not len(pos):
        return float("nan")
    thr = pos[max(0, int(np.floor((1 - tpr_target) * len(pos))) - 1)]
    return float(((p >= thr) & (y == 0)).sum() / max(1, (y == 0).sum()))


def run(out_dir: str = "bench_cargo", n_per_class: int | None = None, esm_model: str | None = None) -> dict:
    import numpy as np
    np.random.seed(SEED)
    n_per_class = n_per_class or int(os.environ.get("BF_B2_N", "1200"))
    esm_model = esm_model or os.environ.get("BF_B2_ESM", "esm2_t33_650M_UR50D")
    wd = Path(out_dir)
    wd.mkdir(parents=True, exist_ok=True)

    # 1. data (safe public proxies)
    tox_fa, ben_fa = wd / "toxin.fasta", wd / "benign.fasta"
    if not tox_fa.exists():
        _fetch_fasta("keyword:KW-0800 AND reviewed:true AND length:[50 TO 500]", tox_fa)
    if not ben_fa.exists():
        _fetch_fasta("reviewed:true NOT keyword:KW-0800 AND length:[50 TO 500] AND existence:1", ben_fa)
    tox, ben = _parse_fasta(tox_fa), _parse_fasta(ben_fa)

    def take(d):
        ks = list(d)
        np.random.shuffle(ks)
        return {k: d[k] for k in ks[:n_per_class]}
    tox, ben = take(tox), take(ben)
    seqs = {**tox, **ben}
    label = {**{k: 1 for k in tox}, **{k: 0 for k in ben}}
    (wd / "all.fasta").write_text("".join(f">{k}\n{s}\n" for k, s in seqs.items()))

    # 2. MMseqs2 cluster @40%id -> hold out whole clusters
    mm = wd / "mm"
    mm.mkdir(exist_ok=True)
    subprocess.run(["mmseqs", "easy-cluster", str(wd / "all.fasta"), str(mm / "clu"), str(mm / "tmp"),
                    "--min-seq-id", "0.4", "-c", "0.8", "--cov-mode", "1", "-v", "1"], check=True)
    clu = dict(line.split()[::-1] for line in (mm / "clu_cluster.tsv").read_text().splitlines() if line.split())
    clusters = sorted(set(clu.values()))
    np.random.shuffle(clusters)
    test_clu = set(clusters[:max(1, int(0.3 * len(clusters)))])
    keys = [k for k in seqs if k in clu]
    train_k = [k for k in keys if clu[k] not in test_clu]
    test_k = [k for k in keys if clu[k] in test_clu]

    # 3. ESM2 embeddings (vectors only)
    import esm
    import torch
    model, alphabet = getattr(esm.pretrained, esm_model)()
    model.eval()
    bc = alphabet.get_batch_converter()
    layer = model.num_layers

    def embed(klist):
        out = []
        for k in klist:
            s = seqs[k][:1022]
            _, _, toks = bc([(k, s)])
            with torch.no_grad():
                rep = model(toks, repr_layers=[layer])["representations"][layer]
            out.append(rep[0, 1:len(s) + 1].mean(0).numpy())
        return np.vstack(out)

    Xtr, ytr = embed(train_k), np.array([label[k] for k in train_k])
    Xte, yte = embed(test_k), np.array([label[k] for k in test_k])
    np.savez(wd / "vectors.npz", Xtr=Xtr, ytr=ytr, Xte=Xte, yte=yte)   # VECTORS ONLY — sequences not persisted

    # 4-5. trained head + metrics (cluster-bootstrap CIs)
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import average_precision_score, roc_auc_score
    clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Xtr, ytr)
    pte = clf.predict_proba(Xte)[:, 1]
    tcl = np.array([clu[k] for k in test_k])

    def boot(fn, reps=1000):
        uc = list(set(tcl))
        rng = np.random.RandomState(SEED)
        vals = []
        for _ in range(reps):
            idx = np.concatenate([np.where(tcl == c)[0] for c in rng.choice(uc, len(uc), replace=True)])
            vals.append(fn(yte[idx], pte[idx]))
        v = np.array(sorted(x for x in vals if x == x))
        return [round(float(np.percentile(v, 2.5)), 3), round(float(np.percentile(v, 97.5)), 3)]

    esm_metrics = {"TPR@1%FPR": round(_tpr_at_fpr(yte, pte), 3), "TPR@1%FPR_CI": boot(_tpr_at_fpr),
                   "FPR@95%TPR": round(_fpr_at_tpr(yte, pte), 3), "AUROC": round(roc_auc_score(yte, pte), 3),
                   "AUPRC": round(average_precision_score(yte, pte), 3)}

    # 4b. homology baseline (mmseqs search test -> train toxins)
    (wd / "tox_train.fasta").write_text("".join(f">{k}\n{seqs[k]}\n" for k in train_k if label[k] == 1))
    (wd / "test.fasta").write_text("".join(f">{k}\n{seqs[k]}\n" for k in test_k))
    res = mm / "hom.m8"
    subprocess.run(["mmseqs", "easy-search", str(wd / "test.fasta"), str(wd / "tox_train.fasta"), str(res),
                    str(mm / "tmp2"), "--min-seq-id", "0.0", "-c", "0.3", "--cov-mode", "1", "-v", "1",
                    "--format-output", "query,pident"], check=True)
    best: dict[str, float] = {}
    if res.exists():
        for line in res.read_text().splitlines():
            q, pid = line.split()[0], float(line.split()[1])
            best[q] = max(best.get(q, 0.0), pid / 100.0 if pid > 1 else pid)
    hom = np.array([best.get(k, 0.0) for k in test_k])
    hom_metrics = {"TPR@1%FPR": round(_tpr_at_fpr(yte, hom), 3),
                   "AUROC": round(roc_auc_score(yte, hom) if len(set(hom)) > 1 else 0.5, 3)}

    # 6. shortcut probes
    def comp(s):
        return np.array([s.count(a) for a in AAS], float) / max(1, len(s))
    probes = {}
    for name, Atr, Ate in [
        ("length", np.array([[len(seqs[k])] for k in train_k]), np.array([[len(seqs[k])] for k in test_k])),
        ("composition", np.vstack([comp(seqs[k]) for k in train_k]), np.vstack([comp(seqs[k]) for k in test_k]))]:
        c = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Atr, ytr)
        pr = c.predict_proba(Ate)[:, 1]
        probes[name] = {"AUROC": round(roc_auc_score(yte, pr), 3), "TPR@1%FPR": round(_tpr_at_fpr(yte, pr), 3)}

    result = {
        "n_train": len(train_k), "n_test": len(test_k),
        "n_clusters": len(clusters), "n_test_clusters": len(test_clu),
        "esm_model": esm_model, "esm_head": esm_metrics, "homology_baseline": hom_metrics,
        "shortcut_probes": probes,
        "gate_pass": esm_metrics["TPR@1%FPR"] > hom_metrics["TPR@1%FPR"]
                     and esm_metrics["TPR@1%FPR_CI"][0] > hom_metrics["TPR@1%FPR"],
        "seed": SEED,
    }
    (wd / "results.json").write_text(json.dumps(result, indent=2))
    return result
