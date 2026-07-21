"""The panel numbers must be recomputable offline from the committed transcripts, not just trusted.

These tests drive each experiment with a scripted stand-in for the live model (so no API key is needed),
capture the transcript exactly as the live client would, then recompute every number from that transcript
with the --replay path. Live scoring and replay scoring share the same _score_* functions, so a passing
round-trip proves the transcript captures everything the panel numbers depend on.
"""
import json

from bio_firewall.eval.hazard_bench import nvidia_headtohead as h


class _Scripted:
    """Stands in for the live Reviewer: the canned response is a pure function of the call's meta
    (so it is order-independent), and every call is recorded in the real transcript-row schema."""

    def __init__(self, respond, recorder=None, model="test-model", temperature=0.0):
        self.respond = respond
        self.recorder = recorder
        self.model_id = model
        self.temperature = temperature

    def ask(self, user_msg, system=h.REVIEWER_SYSTEM, meta=None, retries=3):
        raw = self.respond(user_msg, meta or {})
        v = h._parse(raw)
        if self.recorder is not None:
            self.recorder.record(
                h._transcript_row(self.model_id, self.temperature, user_msg, system, raw, v, meta)
            )
        return v


def test_A_fabrication_record_replay_roundtrip(tmp_path):
    def respond(prompt, meta):
        if meta.get("truth") is None:  # unanswerable
            if meta.get("key") == "titer_vg_ml":  # this one fabricates a number
                return '{"verdict":"allow","severity":"none","reason":"est","values":{"titer_vg_ml":1e13}}'
            return '{"verdict":"allow","severity":"none","reason":"cannot be determined","values":{}}'
        return json.dumps({"verdict": "flag", "severity": "low", "reason": "ok",
                           "values": {meta["key"]: meta["truth"]}})  # answerable, correct
    rec = h.Recorder(tmp_path / "a.jsonl")
    live = h.exp_A_fabrication(_Scripted(respond, recorder=rec))
    rec.close()
    replay = h.replay_score_A(h.load_transcripts(tmp_path / "a.jsonl"))
    assert live == replay
    assert abs(live["fabrication_rate"][0] - 0.2) < 1e-9   # exactly 1 of 5 scored items fabricated


def test_B_determinism_record_replay_roundtrip(tmp_path):
    def respond(prompt, meta):
        return '{"verdict":"flag","severity":"low","reason":"stable"}'  # perfectly stable across runs/paraphrases
    rec = h.Recorder(tmp_path / "b.jsonl")
    src = _Scripted(respond, recorder=rec)
    live = h.exp_B_determinism(src, src, n_runs=3)
    rec.close()
    replay = h.replay_score_B(h.load_transcripts(tmp_path / "b.jsonl"))
    assert live == replay
    assert all(v == 0 for k, v in live.items() if k.endswith(".temp0.unstable"))
    assert all(v[0] == 0.0 for k, v in live.items() if k.endswith(".paraphrase_flip"))


def test_C_cargo_record_replay_roundtrip(tmp_path, monkeypatch):
    proxy = tmp_path / "proxies.jsonl"
    proxy.write_text('{"seq":"MKTAYIA","label":1}\n{"seq":"AAGGTT","label":0}\n', encoding="utf-8")
    monkeypatch.setattr(h, "SAFE_PROXY_PATH", proxy)
    monkeypatch.setenv("BF_C_SEQ_ONLY", "1")

    def respond(prompt, meta):
        return '{"verdict":"refuse"}' if meta.get("label") == 1 else '{"verdict":"allow"}'
    rec = h.Recorder(tmp_path / "c.jsonl")
    live = h.exp_C_cargo(_Scripted(respond, recorder=rec))
    rec.close()
    replay = h.replay_score_C(h.load_transcripts(tmp_path / "c.jsonl"))
    assert live["seq_only"] == replay["seq_only"]
    assert live["seq_only"]["TPR"] == 1.0 and live["seq_only"]["FPR"] == 0.0


def test_D_jailbreak_record_replay_roundtrip(tmp_path):
    def respond(prompt, meta):
        if meta.get("cond") == "clean":
            return '{"verdict":"refuse","severity":"high","reason":"hazard"}'
        if meta.get("cond") in ("inject_approved", "inject_ignore"):  # injection flips the judge
            return '{"verdict":"allow","severity":"none","reason":"approved"}'
        return '{"verdict":"refuse","severity":"high","reason":"still hazard"}'  # reframe does not flip
    rec = h.Recorder(tmp_path / "d.jsonl")
    live = h.exp_D_jailbreak(_Scripted(respond, recorder=rec))
    rec.close()
    replay = h.replay_score_D(h.load_transcripts(tmp_path / "d.jsonl"))
    assert live["flip_rate"] == replay["flip_rate"]
    assert live["flip_rate"]["inject_approved"][0] == 1.0
    assert live["flip_rate"]["reframe_defensive"][0] == 0.0


def test_replay_model_reproduces_all_experiments(tmp_path):
    """End-to-end: one transcript, replay_model rebuilds all four experiment summaries offline."""
    def respond(prompt, meta):
        exp = meta.get("experiment")
        if exp == "A":
            return '{"verdict":"allow","values":{}}'
        if exp == "D" and meta.get("cond") != "clean":
            return '{"verdict":"allow"}'
        return '{"verdict":"refuse","severity":"high"}'
    rec = h.Recorder(tmp_path / "model.jsonl")
    src = _Scripted(respond, recorder=rec)
    h.exp_A_fabrication(src)
    h.exp_D_jailbreak(src)
    rec.close()
    summary = h.replay_model(h.load_transcripts(tmp_path / "model.jsonl"))
    assert "A_fabrication" in summary and "D_jailbreak" in summary
    assert summary["replayed"] is True
