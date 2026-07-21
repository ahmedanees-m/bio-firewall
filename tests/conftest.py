"""Shared test fixtures.

The screening path carries module-level ``lru_cache``s: ``cargo._guardian`` (the PEN-STACK
Guardian decision, keyed by cargo function), ``cargo_ml._centroids`` / ``cargo_ml._model`` (the
ESM-2 reference loaders), and ``kb.registry.load_kb`` (the signed hazard-KB release). Those caches persist across tests, so one test can inherit another test's
cached state. That is a correctness hazard for the security test ``test_redteam_no_flip_to_allow``:
its refuse decisions must not depend on whether an earlier test happened to warm ``_guardian`` while
the Guardian was momentarily unavailable (which caches a ``None`` miss and turns a refuse into a
fall-through ``clear``). Clearing the caches before every test makes each start from a cold,
deterministic state, so the suite is order-independent and safe to run under randomized ordering.
"""
import pytest


@pytest.fixture(autouse=True)
def _clear_cargo_caches():
    from bio_firewall.hazard import cargo, cargo_ml
    from bio_firewall.kb import registry

    for cached in (cargo._guardian, cargo_ml._centroids, cargo_ml._model, registry.load_kb):
        cached.cache_clear()
    yield
