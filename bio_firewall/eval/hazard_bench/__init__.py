"""Benchmark 1 — de-circularized structural-hazard interception (the headline).

Run:  python -c "from bio_firewall.eval.hazard_bench import run_benchmark1, summary; print(summary(run_benchmark1()))"
B1 (frontier) verdicts are loaded from BF_B1_VERDICTS (a JSON {gene: decision}) if present; otherwise B1 is skipped."""
from __future__ import annotations

import json
import os

from bio_firewall.adapters.generic_artifact import normalize
from bio_firewall.intercept.spine import screen

from . import baselines, generate, oracles, score


def run_benchmark1(seed: int = 1234, b1_path: str | None = None) -> dict:
    rows = generate.generate(seed=seed)
    b1 = baselines.load_b1_verdicts(b1_path or os.environ.get("BF_B1_VERDICTS", ""))
    for r in rows:
        plan = r["plan"]
        v = screen(plan)
        r["fw"] = v["decision"]
        r["conf"] = v.get("confidence", "high")
        r["abstain"] = bool(v.get("abstain"))
        r["b0"] = baselines.b0_homology_screen(normalize(plan))
        r["b1"] = b1.get(r["gene"])      # None unless this gene was in the frontier sample
    result = score.score(rows)
    result["oracles"] = oracles.oracle_status()
    result["strata_counts"] = generate.stratum_counts(rows)
    result["seed"] = seed
    result["_rows"] = rows               # retained for B1-sampling / calibration / report
    return result


def summary(result: dict) -> str:
    o = result["overall"]
    lines = [
        "=== BioFirewall Benchmark 1 — de-circularized structural-hazard interception ===",
        f"oracles: {result['oracles']}",
        f"strata : {result['strata_counts']}",
        "",
        f"OVERALL firewall interception of INDEPENDENT hazard label (Tier-1 ∪ COSMIC CGC): "
        f"{o['firewall_interception']:.1%}  CI{o['firewall_ci']}  (n={o['n_hazard']})",
        f"  B0 homology floor: {o['b0_homology_interception']:.1%}"
        + (f"   |  B1 frontier: {o['b1_frontier_interception']:.1%} (n={o['b1_n']})"
           if o['b1_frontier_interception'] is not None else "   |  B1 frontier: not yet run"),
        "",
        "by stratum (firewall | B0 | B1 | lift):",
    ]
    for s, d in sorted(result["by_stratum"].items()):
        b1s = f"{d['b1_frontier']:.0%}" if d["b1_frontier"] is not None else "--"
        lines.append(f"  {s:<26} n={d['n']:<4} fw={d['firewall']:.0%} CI{d['firewall_ci']}  "
                     f"B0={d['b0_homology']:.0%}  B1={b1s}  lift={d['lift_vs_max_baseline']:+.0%}")
    t = result["tier1_gold"]
    u = result["usability"]
    fa = result["failure_analysis"]
    lines += [
        "",
        f"TIER-1 GOLD (clinical insertional-oncogenesis): {t['caught']}/{t['n']} caught  "
        f"-> {'PASS (100%)' if t['pass'] else 'FAIL'}",
        f"USABILITY: false-refuse on legitimate research = {u['false_refuse_n']}/{u['n_legit_research']} "
        f"({u['false_refuse_rate']:.1%})  [deployment gate: 0]   "
        f"false-flag on clearly-benign = {u['false_flag_n']}/{u['n_clean_negatives']} ({u['false_flag_rate']:.1%})",
        f"  dosage-sensitive negatives (flagging is CORRECT): {u['dosage_sensitive']['flagged_correctly']}/"
        f"{u['dosage_sensitive']['n']} flagged, {u['dosage_sensitive']['wrongly_refused']} wrongly refused",
        f"FAILURE ANALYSIS: firewall missed {fa['n_missed']} independently-hazardous genes "
        f"(honest false-negatives) e.g. {[m['gene'] for m in fa['missed'][:12]]}",
    ]
    return "\n".join(lines)


def dump_b1_sample(result: dict, path: str, per_stratum: int = 40, seed: int = 99) -> dict:
    """Pre-registered stratified sample of plans for the blind frontier reviewer (cost control). Writes a JSON of
    {gene: {prompt, stratum, plan}} the orchestrator runs through Claude sub-agents; returns the sample dict."""
    import random
    rng = random.Random(seed)
    by_s: dict[str, list] = {}
    for r in result["_rows"]:
        by_s.setdefault(r["stratum"], []).append(r)
    sample: dict[str, dict] = {}
    for s, rs in by_s.items():
        pick = rs if len(rs) <= per_stratum else rng.sample(rs, per_stratum)
        for r in pick:
            sample[r["gene"]] = {"stratum": s, "plan": r["plan"], "prompt": baselines.b1_prompt_for(r["plan"])}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sample, f, indent=2)
    return sample
