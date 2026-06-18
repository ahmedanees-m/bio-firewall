"""P9 - the managed/tiered access plane (v0.8.0, WS-MANAGED).

Implements NTI's second design-stage guardrail (managed access by risk + user legitimacy), so BioFirewall covers
the complete recommended set: built-in screening (P2) + signed metadata (P4) + managed access (P9). It composes with
the planes already present; it gates the RESOLUTION of a verdict, not the verdict itself.

The credentialing AUTHORITY is a documented integration point - the deployment supplies it through a verification
hook. This plane provides the enforcement MECHANISM; it does not claim to BE a credentialing authority.
"""
from bio_firewall.access.managed import (  # noqa: F401
    LEGITIMACY,
    RESOLUTIONS,
    apply_access,
    resolve,
    screen_managed,
    verify_access,
)

__all__ = ["LEGITIMACY", "RESOLUTIONS", "apply_access", "resolve", "screen_managed", "verify_access"]
