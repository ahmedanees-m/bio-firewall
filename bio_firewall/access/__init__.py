"""P9: the managed/tiered access plane.

Implements NTI's second design-stage guardrail (managed access by risk + user legitimacy), so BioFirewall covers
the complete recommended set: built-in screening (P2) + signed metadata (P4) + managed access (P9). It composes with
the planes already present; it gates the RESOLUTION of a verdict, not the verdict itself.

The credentialing AUTHORITY is a documented integration point - the deployment supplies it through a verification
hook. This plane provides the enforcement MECHANISM; it does not claim to BE a credentialing authority.
"""
from bio_firewall.access.managed import (  # noqa: F401
    EXECUTABLE_RESOLUTIONS,
    LEGITIMACY,
    RESOLUTIONS,
    access_resolution,
    apply_access,
    resolution_permits_execution,
    resolve,
    screen_managed,
    verify_access,
)

__all__ = ["EXECUTABLE_RESOLUTIONS", "LEGITIMACY", "RESOLUTIONS", "access_resolution", "apply_access",
           "resolution_permits_execution", "resolve", "screen_managed", "verify_access"]
