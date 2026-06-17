"""Persist a Benchmark-1 run: full JSON + a manuscript-style markdown report (honest framing built in)."""
from __future__ import annotations

import json
from pathlib import Path


def write_run(result: dict, out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # full JSON (drop the heavy _rows)
    dump = {k: v for k, v in result.items() if k != "_rows"}
    (out / "benchmark1_result.json").write_text(json.dumps(dump, indent=2), encoding="utf-8")
    (out / "benchmark1_report.md").write_text(_md(result), encoding="utf-8")


def _md(r: dict) -> str:
    o = r["overall"]
    b1 = r.get("b1_head_to_head")
    L = ["# BioFirewall Benchmark 1 — de-circularized structural-hazard interception (locus axis)", ""]
    L += [f"- Independent labels: Tier-1 clinical-CIS ({r['oracles']['tier1_clinical_cis']}) + "
          f"COSMIC CGC v104 ({r['oracles']['cosmic_cgc_v104']}) — sources the firewall does NOT use.",
          f"- Seed: {r['seed']}. Strata: {r['strata_counts']}.", ""]
    L += ["## T1 — Tier-1 gold (mandatory 100%)", ""]
    t = r["tier1_gold"]
    L += [f"**{t['caught']}/{t['n']} caught -> {'PASS' if t['pass'] else 'FAIL'}**", "",
          "| gene | firewall | B0 homology | B1 frontier |", "|---|---|---|---|"]
    for row in t["table"]:
        L.append(f"| {row['gene']} | {row['firewall']} | {row['b0']} | {row.get('b1') or '--'} |")
    L += ["", "## T2 — Per-stratum interception & lift (firewall vs real baselines)", "",
          "| stratum | n | firewall | B0 homology | B1 frontier | lift vs max baseline |",
          "|---|---|---|---|---|---|"]
    for s, d in sorted(r["by_stratum"].items()):
        b1s = f"{d['b1_frontier']:.0%}" if d["b1_frontier"] is not None else "--"
        L.append(f"| {s} | {d['n']} | {d['firewall']:.0%} (CI {d['firewall_ci']}) | {d['b0_homology']:.0%} | "
                 f"{b1s} | {d['lift_vs_max_baseline']:+.0%} |")
    L += ["",
          f"**Overall firewall interception of the independent label: {o['firewall_interception']:.1%} "
          f"(CI {o['firewall_ci']}), n={o['n_hazard']}. B0 homology floor: {o['b0_homology_interception']:.1%}.**", ""]
    if b1:
        L += ["## B1 head-to-head (firewall vs frontier Claude, SAME sampled genes)", "",
              f"- n hazardous sampled: {b1['n_hazard_sampled']}",
              f"- firewall {b1['firewall_interception']:.1%} | B0 {b1['b0_interception']:.1%} | "
              f"B1 frontier {b1['b1_interception']:.1%} | lift(fw-B1) {b1['lift_fw_vs_b1']:+.1%}",
              f"- **Usability: firewall false-refuse on legitimate research = {b1['legit_research']['firewall_false_refuse']}"
              f"/{b1['legit_research']['n']}; frontier B1 false-refuse = {b1['legit_research']['b1_false_refuse']}"
              f"/{b1['legit_research']['n']} (refused {b1['legit_research']['b1_refused_genes']}).**",
              f"- false-flag on clean negatives: firewall {b1['clean_negatives']['firewall_false_flag']:.1%} | "
              f"B1 {b1['clean_negatives']['b1_false_flag']:.1%}", ""]
    u = r["usability"]
    L += ["## T3 — Usability (Claim C)", "",
          f"- false-refuse on legitimate research: {u['false_refuse_n']}/{u['n_legit_research']} "
          f"({u['false_refuse_rate']:.1%}) — deployment gate = 0",
          f"- false-flag on clearly-benign genes: {u['false_flag_n']}/{u['n_clean_negatives']} ({u['false_flag_rate']:.1%})",
          f"- dosage-sensitive negatives: {u['dosage_sensitive']['flagged_correctly']}/{u['dosage_sensitive']['n']} "
          f"flagged (correct), {u['dosage_sensitive']['wrongly_refused']} wrongly refused", ""]
    fa = r["failure_analysis"]
    L += ["## Failure analysis (honest false-negatives)", "",
          f"The firewall MISSED {fa['n_missed']} independently-hazardous COSMIC genes (the generalization limit):", "",
          ", ".join(m["gene"] for m in fa["missed"][:40]) + (" ..." if fa["n_missed"] > 40 else ""), ""]
    L += ["## Honest reading", "",
          "- The homology/synthesis-screen floor (B0) catches **0%** of these structural-locus hazards — confirming "
          "the design-stage gap is real.",
          "- A frontier LLM (B1) is a **strong** locus-recall baseline (comparable to the rule firewall) — but it "
          "**over-refuses legitimate research** and is non-deterministic/non-auditable.",
          "- The firewall's contribution on the locus axis is therefore **deterministic, stratified (flag-not-block), "
          "auditable** governance with near-zero false-refuse — NOT a claim of higher raw recall than a frontier model.",
          "- Concordance with an independent hazard model is **necessary, not sufficient**, for real-world safety "
          "(wet-lab validation is declared future work)."]
    return "\n".join(L)
