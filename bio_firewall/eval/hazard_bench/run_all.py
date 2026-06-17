"""Driver: run Benchmark 1 (structural-hazard, de-circularized) + Benchmark 3 (red-team) + Benchmark 4
(calibration), persist JSON + reports. Benchmark 2 (cargo ML) runs separately on the GPU VM (cargo_bench/).

Env: PEN_STACK_HOME (Guardian configs), BF_BENCH_ORACLES (COSMIC etc.), BF_B1_VERDICTS (frontier sample)."""
from __future__ import annotations

import json
from pathlib import Path


def main(out_dir: str) -> dict:
    from bio_firewall.eval.hazard_bench import run_benchmark1, summary
    from bio_firewall.eval.hazard_bench.calibrate_bench import run_calibration
    from bio_firewall.eval.hazard_bench.redteam import run_redteam
    from bio_firewall.eval.hazard_bench.report import write_run

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    b1 = run_benchmark1()
    write_run(b1, out_dir)
    print(summary(b1))

    b3 = run_redteam()
    (out / "benchmark3_redteam.json").write_text(json.dumps(b3, indent=2), encoding="utf-8")
    print(f"\n[B3 red-team] {b3['total_trials']} attacks, flip-rate(refuse->allow)="
          f"{b3['overall_flip_rate']:.0%}, grounding-violations={len(b3['grounding_violations'])} -> "
          f"{'PASS' if b3['pass'] else 'FAIL'}")

    b4 = run_calibration(b1["_rows"])
    (out / "benchmark4_calibration.json").write_text(json.dumps(b4, indent=2), encoding="utf-8")
    tier_str = ", ".join(f"{k}:{v['accuracy']}" for k, v in b4["tier_validity"].items())
    print(f"[B4 calibration] tier acc {{ {tier_str} }}; "
          f"hazard-miss(all-allow)={b4['abstention']['hazard_miss_rate_all_allow']:.1%}")

    summary_obj = {
        "benchmark1_overall": b1["overall"],
        "benchmark1_tier1_pass": b1["tier1_gold"]["pass"],
        "benchmark1_b1_head_to_head": b1.get("b1_head_to_head"),
        "benchmark3_pass": b3["pass"],
        "benchmark3_flip_rate": b3["overall_flip_rate"],
        "benchmark4_tier_validity": b4["tier_validity"],
    }
    (out / "SUMMARY.json").write_text(json.dumps(summary_obj, indent=2), encoding="utf-8")
    return summary_obj


if __name__ == "__main__":
    import os
    main(os.environ.get("BF_RUN_DIR", "bench_run"))
