# Qwen End-to-End Benchmark Pipeline (GitHub Actions)

Benchmarks Qwen models served by Ollama on a GitHub-hosted Ubuntu runner and creates **one consolidated report** (`BENCHMARK_SUMMARY.md` plus `benchmark-summary.json`). The report includes each model/quantization's success rate, latency, prompt evaluation time, generated tokens/sec, answer check, context utilization, and case-level details. Raw per-model JSON is retained as a workflow artifact.

> Important: a hosted CPU runner is not a representative GPU benchmark. Model tags, quantization formats and context support vary by Ollama model build. The workflow records model metadata and errors rather than assuming every tag exists. The requested context size is not proof that a model can use that entire context effectively.

## What is tested

- **Model variants:** default matrix includes Qwen3 0.6B, 1.7B, 4B, and a 4B Q8 tag. Change the model list to include any available quantized tags (e.g. Q4_K_M, Q5_K_M, Q8_0) you want compared.
- **Context window:** 512, 1,024, 2,048, 4,096 and 8,192 by default.
- **Input size:** target prompts of 128, 512, 1,024, 2,048 and 4,096 tokens. Actual input token counts are reported by Ollama; targets are approximate because tokenizer tokenization differs.
- **Output caps:** 32, 128 and 512 generated tokens.
- **Performance and behavior:** wall latency, load time, prompt-evaluation time, generation time, tokens/sec, completion count, finish reason, approximate context utilization, process USS/RAM, and a simple sentinel-answer check.
- **Failure handling:** missing model tags and failed inference cases are recorded so one failed variant does not discard the other results.

This is an exhaustive Cartesian sweep of valid `(context, target input, output cap)` combinations for each model, so the default workflow may take hours and download several GB. Use the smoke-test cap for a quick check.

## Run it

1. Push this repository to GitHub.
2. Open **Actions → Qwen end-to-end benchmark → Run workflow**.
3. Set `models` to comma-separated Ollama model tags. The default is `qwen3:0.6b,qwen3:1.7b,qwen3:4b,qwen3:4b-q8_0`. Verify tags are available in the Ollama library before a full run. To compare quantization fairly, use the same base model and include each available quantized tag in this field.
4. Optionally change contexts, input targets, output limits, or set `max_cases_per_model` to e.g. `3` for a quick smoke test (`0` means no cap).
5. When complete, download the `qwen-benchmark-<run_id>` artifact. **`BENCHMARK_SUMMARY.md`** is the human-readable combined report; `benchmark-summary.json` contains the structured version.

## Local use

Requires Python 3.11+, Ollama installed and running, and the selected model already pulled.

```bash
pip install -r requirements.txt
ollama serve
ollama pull qwen3:0.6b
python scripts/bench_ollama.py \
  --model qwen3:0.6b \
  --contexts 512,1024,2048 \
  --input-targets 128,256,512 \
  --output-limits 32,128 \
  --output-json results/qwen3_0.6b.json
python scripts/summarize_results.py
pytest -q
```

## Reading the results responsibly

- Compare models only at matched input, context, output cap and hardware/runtime settings.
- `target_input_tokens` is a prompt-size target; use `prompt_tokens` for the measured count. The prompt builder uses approximate characters/token to avoid requiring model-specific tokenizer libraries.
- A case can fail because the model tag is unavailable, memory is exhausted, the prompt does not fit, or the request times out. Inspect the per-case `error` field.
- Output cap means *maximum* generated tokens, not a promise to generate that many. Inspect `completion_tokens`, `done_reason`, and `output_limit_reached`.
- The sentinel-answer score is a minimal regression check, not a comprehensive language-model quality benchmark. For research-grade quality evaluation, add task datasets and repeat runs with multiple seeds.
- Quantization is inferred from Ollama's returned model metadata. If metadata is missing, the report labels it `unknown` rather than guessing.

## Files

- `.github/workflows/qwen-benchmark.yml` — manual/reusable GitHub Actions workflow.
- `scripts/bench_ollama.py` — context/input/output sweep and runtime measurements.
- `scripts/summarize_results.py` — consolidated Markdown + JSON report generation.
- `tests/` — basic tests for prompt generation and summary generation.
