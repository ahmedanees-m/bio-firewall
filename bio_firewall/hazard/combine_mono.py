"""WS-COMBINE-MONO (v0.6.0) - a PROVABLY-MONOTONE, interaction-aware evidence combiner that replaces the
hand-tuned max-severity cascade.

Two properties a cascade cannot give you together:
  1. MONOTONICITY - adding a hazard finding, or strengthening one, NEVER lowers the combined severity (verified on
     a perturbation suite, `verify_monotone`). This is what makes a stricter screen provably stricter.
  2. CROSS-AXIS INTERACTION - three co-occurring MODERATE signals are more concerning than one. A `max` cascade is
     flat across them; a noisy-OR `1 - prod(1 - r_i)` rises with each signal (and is monotone by construction:
     d/dr_i = prod_{j!=i}(1 - r_j) >= 0).

HARD-RULE EXACTNESS - any `hard_reject` pins severity to 1.0 -> refuse, with NO de-escalation: the soft severity is
capped strictly below the refuse threshold, so soft signals escalate WITHIN the flag tier (a more-urgent review)
but can never auto-refuse legitimate research. Decisions are therefore IDENTICAL to the v0.5 cascade
(hard->refuse, any-soft->flag, none->allow) - only a richer, monotone, auditable SEVERITY is added.
"""
from __future__ import annotations

from bio_firewall.hazard.finding import SEVERITY

# per-finding base risk (continuous). hard_reject is pinned; soft tiers ordered scope_flag > soft_penalty.
_BASE = {"hard_reject": 1.0, "scope_flag": 0.60, "soft_penalty": 0.30, "clear": 0.0}
# named-positive locus evidence is weightier than a dosage-only flag (still soft) - a small, documented bump.
_STRONG = {"locus.genotoxic_proximity", "locus.tumor_suppressor_disruption", "locus.oncogene_proximity",
           "edit.fusion_unknown_oncogenicity"}
FLAG_THRESHOLD = 0.30        # severity >= this -> flag (a single soft_penalty reaches it -> decisions unchanged)
REFUSE_THRESHOLD = 0.90      # severity >= this -> refuse (only a hard_reject reaches it)
FLAG_CEILING = 0.88          # soft severity is capped here (< REFUSE_THRESHOLD): soft signals never auto-refuse


def axis_risk(finding) -> float:
    """Continuous risk of one finding in [0,1]. dict or Finding accepted."""
    dec = finding["decision"] if isinstance(finding, dict) else finding.decision
    rid = (finding.get("rule_id") if isinstance(finding, dict) else finding.rule_id) or ""
    r = _BASE.get(dec, 0.0)
    if dec in ("soft_penalty", "scope_flag") and rid in _STRONG:
        r = min(0.75, r + 0.10)
    return r


def monotone_severity(findings) -> tuple[float, str]:
    """Combine per-axis risks into (severity, decision). Noisy-OR over soft risks (monotone + interaction-aware);
    any hard_reject pins severity to 1.0 (refuse, exact). Soft severity is capped below REFUSE_THRESHOLD."""
    risks = [axis_risk(f) for f in findings]
    if any(r >= 1.0 for r in risks):
        return 1.0, "refuse"
    prod = 1.0
    for r in risks:
        prod *= (1.0 - r)
    sev = min(1.0 - prod, FLAG_CEILING)              # noisy-OR, capped strictly below the refuse threshold
    decision = "refuse" if sev >= REFUSE_THRESHOLD else ("flag_for_review" if sev >= FLAG_THRESHOLD else "allow")
    return round(sev, 4), decision


# --------------------------------------------------------------------------------------------------------------
# verification (the proof the gate checks): monotone + hard-rule-exact on a perturbation suite
# --------------------------------------------------------------------------------------------------------------
def _fset(decisions, rule_ids=None):
    rule_ids = rule_ids or [None] * len(decisions)
    return [{"decision": d, "rule_id": r} for d, r in zip(decisions, rule_ids)]


def verify_monotone(reps: int = 5000, seed: int = 1234) -> dict:
    """PERTURBATION SUITE: for random finding-sets, (a) adding any finding never lowers severity, (b) upgrading any
    finding's decision to a stricter tier never lowers severity, (c) any hard_reject => refuse exactly."""
    import random
    rng = random.Random(seed)
    tiers = ["clear", "soft_penalty", "scope_flag", "hard_reject"]
    add_ok = up_ok = hard_ok = 0
    n_add = n_up = n_hard = 0
    for _ in range(reps):
        k = rng.randint(0, 5)
        base = _fset([rng.choice(tiers[:3]) for _ in range(k)])            # soft/clear base set
        s0, _ = monotone_severity(base)
        # (a) add a finding
        added = base + _fset([rng.choice(tiers)])
        s1, d1 = monotone_severity(added)
        n_add += 1
        add_ok += int(s1 >= s0 - 1e-9)
        # (b) upgrade one finding's tier (if any)
        if base:
            i = rng.randrange(len(base))
            cur = tiers.index(base[i]["decision"])
            if cur < 3:
                up = [dict(f) for f in base]
                up[i]["decision"] = tiers[cur + 1]
                s2, _ = monotone_severity(up)
                n_up += 1
                up_ok += int(s2 >= s0 - 1e-9)
        # (c) hard-rule exactness
        if any(f["decision"] == "hard_reject" for f in added):
            n_hard += 1
            hard_ok += int(d1 == "refuse")
    return {
        "reps": reps,
        "monotone_under_addition": add_ok == n_add, "n_add": n_add,
        "monotone_under_upgrade": up_ok == n_up, "n_up": n_up,
        "hard_rule_exact_refuse": (n_hard == 0) or (hard_ok == n_hard), "n_hard": n_hard,
        "provably_monotone": (add_ok == n_add) and (up_ok == n_up),
        "thresholds": {"flag": FLAG_THRESHOLD, "refuse": REFUSE_THRESHOLD, "flag_ceiling": FLAG_CEILING},
    }


def decision_matches_cascade(findings) -> bool:
    """Equivalence guard: the monotone combiner's DECISION must equal the v0.5 max-severity cascade's decision."""
    worst = max((SEVERITY[f["decision"] if isinstance(f, dict) else f.decision] for f in findings), default=0)
    cascade = "refuse" if worst >= 3 else ("flag_for_review" if worst >= 1 else "allow")
    return monotone_severity(findings)[1] == cascade
