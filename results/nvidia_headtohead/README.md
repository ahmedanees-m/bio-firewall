# Control-vs-advisor panel: frozen results

These are the frozen results of the control-vs-advisor panel (docs/PANEL.md) as measured on 2026-06-17 against
open models via NVIDIA's OpenAI-compatible NIM endpoint. The prompt, rubric, abstention option, temperature, and
model set were fixed before scoring; the numbers here are the ones reported in docs/HEADTOHEAD.md and the manuscript.

- `summary.json` - all models, all experiments, in one object.
- `deepseek.json`, `llama.json`, `qwen.json` - per-model results.

Each file carries, per experiment, the computed rates with bootstrap confidence intervals and the per-call parsed
verdicts (the `detail` / `rows` arrays). This run covered experiments A (fabrication), B (determinism), and D
(jailbreak-judge); the cargo experiment C is a separate benchmark (see docs/HEADTOHEAD.md and the cargo gate).

Headline (D, jailbreak): prompt-injection flips `refuse -> allow` on the open judges (llama 0.50 / 0.83; qwen 0.83 /
0.50) while reframing alone flips 0.00 and the firewall is 0% by construction. A (fabrication) did not recur (all
models abstain on the unanswerable set) and B (determinism) was stable, so both were reported as withdrawn.

**Raw responses.** The 2026-06-17 harness recorded the parsed verdicts and the computed rates, not the raw model
response text. The current harness (`bio_firewall/eval/hazard_bench/nvidia_headtohead.py`) adds a capture step that
records every call verbatim to `transcripts/<model>.jsonl` and an offline `--replay` mode that recomputes every number
from those transcripts (round-trip covered by `tests/test_headtohead_replay.py`), so any faithful re-run is
byte-reproducible with no API key. The numbers above stand as the frozen, pre-registered measurement.
