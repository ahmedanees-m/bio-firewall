# Gating the PEN-STACK cloud-lab execution bridge

PEN-STACK added a design->physical-execution path: `pen_stack.build.cloudlab.submit(design, experiment,
...)` (raises `ProtocolExportError` when its own in-design gate blocks), `submit_gated(...)` (returns a structured
refusal instead of raising), and the `cloudlab_submit` MCP tool that routes to `submit_gated`. The endpoint is
mock/dry-run today, but the path exists. PEN-STACK's own gate is the necessary-not-sufficient in-design screen;
BioFirewall is **the comprehensive downstream screen** that must run first, in-workflow, where an agent
cannot route around it.

## The interception contract

`bio_firewall.adapters.cloudlab_gate.gated_cloudlab_submit(design, experiment, *, passport=None, submit_fn=None,
audit=None, **submit_kw)`:

- **allow** -> the design is submitted, carrying the BioFirewall passport in the experiment record; PEN-STACK's own
  gate still runs underneath (defense in depth).
- **flag_for_review** -> held for human review; nothing is submitted.
- **refuse** -> blocked; nothing is submitted.
- A **tampered passport** (HMAC fails) or a passport **reused on a different design** (the `inputs_hash` does not match)
  is rejected; nothing is submitted - even if PEN-STACK's own gate would have allowed it.

The gate decision and the design hash are written to the hash-chained audit log (tamper-evident). `submit_fn` defaults
to PEN-STACK's `submit_gated` (lazy, guarded import, mirroring the cargo axis's coupling); inject a stub in tests.

Two modes: with no `passport`, the design is screened fresh (the normal in-workflow path) and the minted passport is
carried; with a `passport` carried from an earlier `screen()`, it is verified against this design and only an intact,
matching `allow` passport proceeds.

## Example

```python
from bio_firewall.adapters.cloudlab_gate import gated_cloudlab_submit
from bio_firewall.audit.log import AuditLog

log = AuditLog()
result = gated_cloudlab_submit(
    {"intent": "insert a Factor IX cassette", "gene": "AAVS1", "cell_type": "hepatocyte"},
    {"target": "opentrons"}, audit=log)         # -> submit_fn = pen_stack.build.cloudlab.submit_gated by default
# result["submitted"] is True only on a verified allow passport; the audit chain records the gate decision.
```

## Scope and limits

The gate is the **mechanism**, not a deployed execution authority. PEN-STACK's cloud-lab endpoint is mock/dry-run, so
the tests assert the interception contract (nothing reaches submission without a verified `allow` passport), not a real
wet run. Real-execution enforcement is pending a real cloud-lab provider - the same standing bottleneck PEN-STACK
surfaces. The gate governs PEN-STACK via the adapter and does not modify it.
