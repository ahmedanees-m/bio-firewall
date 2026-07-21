"""P8 - bind conformal-style confidence + abstention to the hazard verdict (legality != confidence).

Confidence tiers (no fabricated probability): a DETERMINISTIC rule match (Select-Agent cargo, human-heritable-clinical,
a known oncogenic fusion) is HIGH confidence; a data-grounded MECHANISM flag (oncogene/TSG/essential/dosage/genotox
proximity - extrapolating, not outcome-validated) is MODERATE; a PROBABILISTIC/ML signal (function-aware ESM) is LOW.
A low-confidence ALLOW is ESCALATED to flag_for_review - we do not confidently clear what we cannot confidently
assess (lower the abstention threshold under uncertainty)."""
from __future__ import annotations

from bio_firewall.hazard.finding import SEVERITY

_DETERMINISTIC = {
    "cargo.select_agent_or_toxin", "cargo.gene_drive", "germline.human_heritable_clinical",
    "germline.human_embryo_research", "edit.oncogenic_fusion_by_design",
}


def calibrate(verdict: dict) -> dict:
    triggered = [f for f in verdict.get("axes", {}).values() if f["decision"] != "clear"]
    if not triggered:
        conf = "high"                                    # clean across all five axes
    else:
        worst = max(triggered, key=lambda f: SEVERITY[f["decision"]])
        if worst.get("rule_id") in _DETERMINISTIC and not worst.get("extrapolating"):
            conf = "high"
        elif worst.get("score") is not None and worst.get("extrapolating"):
            conf = "low"                                 # probabilistic ESM/ML signal
        else:
            conf = "moderate"                            # data-grounded mechanism flag (not outcome-validated)
    verdict["confidence"] = conf
    verdict["abstain"] = abstain = (verdict["decision"] == "allow" and conf == "low")
    if abstain:
        verdict["decision"] = "flag_for_review"
        verdict["reason"] = "low confidence on a clear verdict - escalated to review rather than confidently allowed"
    return verdict
