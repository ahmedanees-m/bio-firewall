"""WS-INTEGRATE (v0.7.0) - the in-workflow gate a design agent wires in so no downstream action (synthesis order,
protocol export) runs without a passing BioFirewall verdict. The agent cannot route around it: `synthesize()` is
hard-gated on an ALLOW verdict with a verifiable passport, and the gate reads the structured artifact, not the
agent's free-text framing."""
from bio_firewall.integrate.agent_gate import (# noqa: F401
    GateBlocked, pre_action_gate, run_gated_loop, synthesize,
)

__all__ = ["pre_action_gate", "synthesize", "run_gated_loop", "GateBlocked"]
