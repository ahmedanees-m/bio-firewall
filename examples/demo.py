"""BioFirewall v0.1 demo — the five-axis screen on representative proxy plans (safe proxies only)."""
from bio_firewall import screen

PLANS = [
    ("benign somatic therapeutic", {"intent": "insert a FIX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"}),
    ("human heritable CLINICAL edit", {"germline": {"cell_type": "zygote", "organism": "human", "clinical": True}}),
    ("human embryo RESEARCH", {"intent": "research", "germline": {"cell_type": "embryo", "organism": "human"}}),
    ("genotoxic-CIS locus (LMO2)", {"intent": "knock-in study", "gene": "LMO2", "cell_type": "hspc"}),
    ("legitimate cancer modeling (TP53)", {"intent": "cancer modeling: disrupt a tumor suppressor", "gene": "TP53"}),
    ("megabase restructuring", {"intent": "large rearrangement", "scale": {"total_bp": 2_000_000}}),
    ("oncogenic fusion by design", {"intent": "make BCR-ABL", "edit": {"fusion": True}}),
]

for label, plan in PLANS:
    v = screen(plan)
    triggered = ", ".join(e["rule_id"] for e in v["evidence"]) or "-"
    print(f"{v['decision']:16}  {label:34}  [{triggered}]")

# the headline experiment: per-axis interception of homology-evading structural hazards (safe proxies).
from bio_firewall.eval import run  # noqa: E402
r = run()
print(f"\nhomology-only baseline interception: {r['homology_baseline_interception']:.0%}"
      f"  |  BioFirewall: {r['overall_interception']:.0%}  |  false-block: {r['false_block_rate']:.0%}")
print("per-axis caught/n:", {a: f"{v['caught']}/{v['n']}" for a, v in r["by_axis"].items()})
