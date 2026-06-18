"""BioFirewall — genome-writing-native biosecurity middleware (v0.1, Phase 0 scaffold).

A supervisor for design AIs, NOT another design tool. It intercepts a genome-writing PLAN and returns a
stratified verdict (allow / flag-for-review / refuse) with cited evidence, across five genome-writing-native
axes: cargo · locus · edit-type · germline · scale. It imports `pen-stack` for reusable machinery and governs
PEN-STACK (and any tool) through the adapter contract.

Honesty (inherited from PEN-STACK): the locus axis FLAGS on mechanism — the genotoxicity proxy is NOT
outcome-validated (PEN-STACK v6.5/v6.6) — it does not predict a cancer rate. Stratification, not a blocklist.
"""
__version__ = "0.6.0"

from bio_firewall.intercept.spine import screen          # noqa: F401  the public entry point

__all__ = ["screen", "__version__"]
