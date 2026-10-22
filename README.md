# Qwen End-to-End Benchmark Pipeline

A reproducible GitHub Actions benchmark for Qwen models served by Ollama. It tests model tags/quantizations, context settings, approximate input sizes, output caps, repeated performance trials, answer extraction, a small quality smoke suite, and failure behavior. It writes a **single consolidated report** (`BENCHMARK_SUMMARY.md`) and machine-readable `benchmark-summary.json`, plus raw per-model JSON.

> **Interpret results carefully:** GitHub-hosted Ubuntu runners are CPU-oriented and shared. They are useful for relative comparisons on the same runner type, not as a proxy for GPU deployment performance. This small built-in quality suite is a smoke test, not a research-grade model evaluation.

## Included tests

- **Model metadata:** Ollama family, parameter size, quantization and format where available.
- **Matrix sweep:** context settings × approximate input targets × output caps, with invalid estimated budgets skipped explicitly.
- **Repeated trials:** median and p95 latency and median/mean throughput in the summary.
- **Prompt and generation telemetry:** actual server-reported prompt/completion tokens, prompt evaluation duration, generation duration, load time, throughput, finish reason, output-cap hit, and context utilization.
- **Answer extraction:** uses Ollama `/api/chat` `message.content`, with legacy `/api/generate` fallback. Sends `think: false` to supported Ollama/Qwen versions so thinking content is not mistaken for the final answer.
- **Quality smoke suite:** capital exact-match, bat-and-ball reasoning, structured output, JSON validity/equality, and a short long-context retrieval check.
- **Position-sensitive retrieval:** beginning/middle/end needle probes at a high requested context/input setting to help detect position-dependent retrieval failures.
- **Position-sensitive retrieval:** beginning/middle/end needle probes at a high requested context/input setting to help detect position-dependent retrieval failures.
- **Output-cap probes:** sustained-generation prompts for each configured output cap; records whether the cap was respected and whether generation likely hit it.
- **Reliability:** errors and skipped context budgets are retained in the result file; one missing model tag does not erase other results.
- **Consolidated report:** model metadata, success/failure counts, quantization, median/p95 latency, throughput, quality score, sentinel score, and full raw case results in JSON.

## Run in GitHub Actions

1. Push the repository to GitHub.
2. Go to **Actions → Qwen end-to-end benchmark → Run workflow**.
3. Start with a smoke run: set `max_cases_per_model` to `3`, contexts to `512,1024`, input targets to `128,256`, output limits to `32,64`, and repeats to `1`.
4. For a full run, use the defaults or customize the model list. Include available tags for each quantization you want to compare; confirm model tags in the Ollama library first.
5. Download the `qwen-benchmark-<run_id>` artifact and open `BENCHMARK_SUMMARY.md`. The JSON summary and raw per-model results are included.

The full default Cartesian matrix can be expensive. Each matrix combination is repeated (2 by default), and a separate quality suite is also run for each model. Increase workflow timeout or reduce the matrix when needed.

## Run locally

Requirements: Python 3.11+, Ollama installed and running, and enough RAM/disk for the selected model.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
ollama pull qwen3:0.6b
python scripts/bench_ollama.py \\
  --model qwen3:0.6b \\
  --contexts 512,1024,2048 \\
  --input-targets 128,256,512 \\
  --output-limits 32,128 \\
  --repeats 2 \\
  --output-json results/qwen3_0.6b.json
python scripts/summarize_results.py
pytest -q
```

Set `OLLAMA_HOST` if Ollama is not listening on `http://127.0.0.1:11434`.

For an optional local GGUF test, install `requirements-llamacpp.txt` in a compatible environment and run `python scripts/bench_llamacpp.py --model-path /path/to/model.gguf --suite full --n-ctx 4096 --output-json results/llamacpp_model.json`.

## Important measurement semantics

- **Input targets are approximate.** The prompt builder uses a character/token heuristic without a model-specific tokenizer. `prompt_tokens_actual` from Ollama is the authoritative observed count. `input_target_error_tokens` quantifies the deviation.
- **Context validation is two-stage.** Cases that cannot fit based on requested target + output cap + safety margin are marked `skipped_budget`. After inference, actual prompt tokens + output cap are checked again. Prompt truncation behavior can vary by model/runtime; this is why both requested and actual values are retained.
- **Output cap is a ceiling, not a target.** `output_cap_reached` shows when the generated count meets the cap. A short answer is not a failure just because it used fewer tokens.
- **TTFT is a proxy.** For non-streaming Ollama responses, the recorded `time_to_first_token_proxy_sec` is load + prompt evaluation time, not a directly observed streaming TTFT.
- **Quality score limitations.** The included deterministic checks are intentionally small and can be fooled by partial answers or ambiguous phrasing. Do not interpret the score as general accuracy. For deeper evaluation, add domain datasets, exact task-specific scoring, multiple seeds, and blinded human review where appropriate.
- **Quantization comparisons.** Check metadata and compare the same base model at matched prompt/context/output settings. Tags such as `qwen3:4b` and `qwen3:4b-q8_0` are only comparable if they really refer to the same model family and revision.
- **Hardware reproducibility.** The report captures Python, OS, logical CPU count, RAM and Ollama version. Keep runner type and runtime consistent between runs.

## Files

- `.github/workflows/qwen-benchmark.yml` — manual and reusable workflow.
- `scripts/bench_ollama.py` — test matrix, API interaction, telemetry and quality checks.
- `scripts/summarize_results.py` — consolidated Markdown and JSON summary.
- `scripts/bench_llamacpp.py` + `scripts/prompts.py` — optional local GGUF benchmark backend (not used by the hosted Ollama workflow); install `requirements-llamacpp.txt` first.
- `tests/test_benchmark.py` — offline tests for extraction, scoring, prompt generation, stats and aggregation.

## What this does not claim

The pipeline does not prove the maximum possible context length of a model, guarantee a full input was attended to, or establish a universal best Qwen variant. It reports the largest **tested and observed** conditions. A stronger context-window study should include position-sensitive retrieval (beginning/middle/end), needle-in-a-haystack distractors, multi-needle questions, and a verified model tokenizer.
