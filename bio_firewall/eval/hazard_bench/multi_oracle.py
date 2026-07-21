"""Multi-oracle de-circularization report: firewall recall against TWO independent cancer-gene censuses (COSMIC CGC
v104 and OncoKB) that the firewall does NOT use, plus the COSMIC-vs-OncoKB DISAGREEMENT analysis (the part).

Each gene gets a benign-cargo plan; the firewall decision is intercept (flag/refuse) or allow. Recall = fraction of
an oracle's genes intercepted. Disagreements (oracle-A-only genes) test whether the firewall generalizes beyond any
single curation."""
from __future__ import annotations

from bio_firewall.eval.hazard_bench import oracles
from bio_firewall.eval.hazard_bench.score import intercepted
from bio_firewall.intercept.spine import screen


def _caught(gene: str) -> bool:
    d = screen({"intent": "insert a benign reporter cassette", "gene": gene,
                "cargo_function": "egfp fluorescent reporter"})["decision"]
    return intercepted(d)


def _recall(genes) -> dict:
    genes = sorted(genes)
    caught = [g for g in genes if _caught(g)]
    return {"n": len(genes), "caught": len(caught),
            "recall": round(len(caught) / len(genes), 3) if genes else None,
            "missed_examples": [g for g in genes if g not in set(caught)][:25]}


def run() -> dict:
    cosmic = set(oracles.cosmic_genes())
    oncokb = set(oracles.oncokb_genes())
    tier1 = set(oracles.tier1_genes())
    if not oncokb or not cosmic:
        return {"error": "need both COSMIC and OncoKB mounted (BF_BENCH_ORACLES)",
                "cosmic": len(cosmic), "oncokb": len(oncokb)}

    out = {
        "oracle_sizes": {"cosmic": len(cosmic), "oncokb": len(oncokb), "tier1": len(tier1),
                         "cosmic&oncokb": len(cosmic & oncokb),
                         "oncokb_only": len(oncokb - cosmic), "cosmic_only": len(cosmic - oncokb)},
        "firewall_recall": {
            "vs_cosmic": _recall(cosmic | tier1),
            "vs_oncokb": _recall(oncokb | tier1),
            "vs_union": _recall(cosmic | oncokb | tier1),
            "vs_consensus_both": _recall(cosmic & oncokb),     # genes BOTH censuses agree are cancer genes
        },
        # the disagreement analysis: does the firewall catch genes unique to each census?
        "disagreement": {
            "oncokb_only_recall": _recall(oncokb - cosmic),    # in OncoKB, not COSMIC
            "cosmic_only_recall": _recall(cosmic - oncokb),    # in COSMIC, not OncoKB
        },
    }
    return out


def summary(r: dict) -> str:
    if "error" in r:
        return f"multi-oracle: {r['error']}"
    s = r["oracle_sizes"]
    fr = r["firewall_recall"]
    dg = r["disagreement"]
    L = ["=== Multi-oracle de-circularization (firewall vs two INDEPENDENT cancer-gene censuses) ===",
         f"oracle sizes: COSMIC {s['cosmic']}, OncoKB {s['oncokb']}, overlap {s['cosmic&oncokb']}, "
         f"OncoKB-only {s['oncokb_only']}, COSMIC-only {s['cosmic_only']}",
         "",
         f"firewall recall vs COSMIC(+Tier1)   : {fr['vs_cosmic']['recall']:.1%}  ({fr['vs_cosmic']['caught']}/{fr['vs_cosmic']['n']})",
         f"firewall recall vs OncoKB(+Tier1)   : {fr['vs_oncokb']['recall']:.1%}  ({fr['vs_oncokb']['caught']}/{fr['vs_oncokb']['n']})",
         f"firewall recall vs UNION(+Tier1)    : {fr['vs_union']['recall']:.1%}  ({fr['vs_union']['caught']}/{fr['vs_union']['n']})",
         f"firewall recall vs CONSENSUS(both)  : {fr['vs_consensus_both']['recall']:.1%}  ({fr['vs_consensus_both']['caught']}/{fr['vs_consensus_both']['n']})",
         "",
         "DISAGREEMENT analysis (generalization to genes unique to ONE census):",
         f"  OncoKB-only genes caught: {dg['oncokb_only_recall']['recall']:.1%}  ({dg['oncokb_only_recall']['caught']}/{dg['oncokb_only_recall']['n']})",
         f"  COSMIC-only genes caught: {dg['cosmic_only_recall']['recall']:.1%}  ({dg['cosmic_only_recall']['caught']}/{dg['cosmic_only_recall']['n']})"]
    return "\n".join(L)
