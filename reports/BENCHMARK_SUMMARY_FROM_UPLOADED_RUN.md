<!-- Recomputed using the improved report generator from the uploaded historical result JSON. The benchmark itself has not been rerun with patched code. -->

# Qwen End-to-End Benchmark Report

Generated UTC: 2026-10-22T07:00:42.055778+00:00

> A successful HTTP request is not proof of useful model quality. Input targets are heuristic; prompt token counts are server-reported. Compare models only on matched hardware, model revisions, prompts, context, and repetitions.

## Executive summary

- Model runs: **4**
- Result records: **560**
- Successful requests: **432**
- Errors: **0**
- Skipped cases: **128**

## Configuration comparison

| Model | Params | Quant | OK | Errors | Median latency s | P95 latency s | Median tok/s | Quality accuracy | Position retrieval | Sentinel accuracy |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen3:0.6b | 751.63M | Q4_K_M | 108 | 0 | 0.0965 | 4.7122 | 79.106 | 0.6 | 1.0 | 1.0 |
| qwen3:1.7b | 2.0B | Q4_K_M | 108 | 0 | 0.1523 | 12.5079 | 38.3675 | 0.8 | 1.0 | 1.0 |
| qwen3:4b-q8_0 | 4.0B | Q8_0 | 108 | 0 | 0.5335 | 47.9267 | 10.4295 | 1.0 | 1.0 | 1.0 |
| qwen3:4b | 4.0B | Q4_K_M | 108 | 0 | 8.9319 | 47.0271 | 14.638 | 0.4 | 0.0 | 0.0 |

## Sentinel retrieval by context and output cap

A short output cap can be exhausted by reasoning before a final answer is emitted. Read these scores alongside completion length and finish reason.

| Model | Context | Output cap | Correct / scored | Accuracy |
|---|---:|---:|---:|---:|
| qwen3:0.6b | 512 | 32 | 2/2 | 1.0 |
| qwen3:0.6b | 512 | 128 | 2/2 | 1.0 |
| qwen3:0.6b | 1024 | 32 | 4/4 | 1.0 |
| qwen3:0.6b | 1024 | 128 | 4/4 | 1.0 |
| qwen3:0.6b | 1024 | 512 | 2/2 | 1.0 |
| qwen3:0.6b | 2048 | 32 | 6/6 | 1.0 |
| qwen3:0.6b | 2048 | 128 | 6/6 | 1.0 |
| qwen3:0.6b | 2048 | 512 | 6/6 | 1.0 |
| qwen3:0.6b | 4096 | 32 | 8/8 | 1.0 |
| qwen3:0.6b | 4096 | 128 | 8/8 | 1.0 |
| qwen3:0.6b | 4096 | 512 | 8/8 | 1.0 |
| qwen3:0.6b | 8192 | 32 | 10/10 | 1.0 |
| qwen3:0.6b | 8192 | 128 | 10/10 | 1.0 |
| qwen3:0.6b | 8192 | 512 | 10/10 | 1.0 |
| qwen3:1.7b | 512 | 32 | 2/2 | 1.0 |
| qwen3:1.7b | 512 | 128 | 2/2 | 1.0 |
| qwen3:1.7b | 1024 | 32 | 4/4 | 1.0 |
| qwen3:1.7b | 1024 | 128 | 4/4 | 1.0 |
| qwen3:1.7b | 1024 | 512 | 2/2 | 1.0 |
| qwen3:1.7b | 2048 | 32 | 6/6 | 1.0 |
| qwen3:1.7b | 2048 | 128 | 6/6 | 1.0 |
| qwen3:1.7b | 2048 | 512 | 6/6 | 1.0 |
| qwen3:1.7b | 4096 | 32 | 8/8 | 1.0 |
| qwen3:1.7b | 4096 | 128 | 8/8 | 1.0 |
| qwen3:1.7b | 4096 | 512 | 8/8 | 1.0 |
| qwen3:1.7b | 8192 | 32 | 10/10 | 1.0 |
| qwen3:1.7b | 8192 | 128 | 10/10 | 1.0 |
| qwen3:1.7b | 8192 | 512 | 10/10 | 1.0 |
| qwen3:4b-q8_0 | 512 | 32 | 2/2 | 1.0 |
| qwen3:4b-q8_0 | 512 | 128 | 2/2 | 1.0 |
| qwen3:4b-q8_0 | 1024 | 32 | 4/4 | 1.0 |
| qwen3:4b-q8_0 | 1024 | 128 | 4/4 | 1.0 |
| qwen3:4b-q8_0 | 1024 | 512 | 2/2 | 1.0 |
| qwen3:4b-q8_0 | 2048 | 32 | 6/6 | 1.0 |
| qwen3:4b-q8_0 | 2048 | 128 | 6/6 | 1.0 |
| qwen3:4b-q8_0 | 2048 | 512 | 6/6 | 1.0 |
| qwen3:4b-q8_0 | 4096 | 32 | 8/8 | 1.0 |
| qwen3:4b-q8_0 | 4096 | 128 | 8/8 | 1.0 |
| qwen3:4b-q8_0 | 4096 | 512 | 8/8 | 1.0 |
| qwen3:4b-q8_0 | 8192 | 32 | 10/10 | 1.0 |
| qwen3:4b-q8_0 | 8192 | 128 | 10/10 | 1.0 |
| qwen3:4b-q8_0 | 8192 | 512 | 10/10 | 1.0 |
| qwen3:4b | 512 | 32 | 0/2 | 0.0 |
| qwen3:4b | 512 | 128 | 0/2 | 0.0 |
| qwen3:4b | 1024 | 32 | 0/4 | 0.0 |
| qwen3:4b | 1024 | 128 | 0/4 | 0.0 |
| qwen3:4b | 1024 | 512 | 0/2 | 0.0 |
| qwen3:4b | 2048 | 32 | 0/6 | 0.0 |
| qwen3:4b | 2048 | 128 | 0/6 | 0.0 |
| qwen3:4b | 2048 | 512 | 0/6 | 0.0 |
| qwen3:4b | 4096 | 32 | 0/8 | 0.0 |
| qwen3:4b | 4096 | 128 | 0/8 | 0.0 |
| qwen3:4b | 4096 | 512 | 0/8 | 0.0 |
| qwen3:4b | 8192 | 32 | 0/10 | 0.0 |
| qwen3:4b | 8192 | 128 | 0/10 | 0.0 |
| qwen3:4b | 8192 | 512 | 0/10 | 0.0 |

## Quality suite by task

| Model | Task | Correct / scored | Accuracy |
|---|---|---:|---:|
| qwen3:0.6b | instruction_three_colors | 2/2 | 1.0 |
| qwen3:0.6b | long_context_retrieval | 0/2 | 0.0 |
| qwen3:0.6b | qa_bat_ball | 0/2 | 0.0 |
| qwen3:0.6b | qa_capital_france | 2/2 | 1.0 |
| qwen3:0.6b | structured_json | 2/2 | 1.0 |
| qwen3:1.7b | instruction_three_colors | 0/2 | 0.0 |
| qwen3:1.7b | long_context_retrieval | 2/2 | 1.0 |
| qwen3:1.7b | qa_bat_ball | 2/2 | 1.0 |
| qwen3:1.7b | qa_capital_france | 2/2 | 1.0 |
| qwen3:1.7b | structured_json | 2/2 | 1.0 |
| qwen3:4b-q8_0 | instruction_three_colors | 2/2 | 1.0 |
| qwen3:4b-q8_0 | long_context_retrieval | 2/2 | 1.0 |
| qwen3:4b-q8_0 | qa_bat_ball | 2/2 | 1.0 |
| qwen3:4b-q8_0 | qa_capital_france | 2/2 | 1.0 |
| qwen3:4b-q8_0 | structured_json | 2/2 | 1.0 |
| qwen3:4b | instruction_three_colors | 2/2 | 1.0 |
| qwen3:4b | long_context_retrieval | 2/2 | 1.0 |
| qwen3:4b | qa_bat_ball | 0/2 | 0.0 |
| qwen3:4b | qa_capital_france | 0/2 | 0.0 |
| qwen3:4b | structured_json | 0/2 | 0.0 |

## Failure diagnostics

Examples below are diagnostic snippets, not a qualitative human evaluation. Inspect raw JSON for full answers.

### qwen3:0.6b
- `qa_bat_ball`; context=2048; output cap=128; completion=52; finish=`stop`; answer=`The bat costs $1.00 more than the ball, so the ball costs:  $$ 1.10 - 1.00 = 0.10 $$  So the ball costs **$0.10**.`
- `qa_bat_ball`; context=2048; output cap=128; completion=52; finish=`stop`; answer=`The bat costs $1.00 more than the ball, so the ball costs:  $$ 1.10 - 1.00 = 0.10 $$  So the ball costs **$0.10**.`
- `long_context_retrieval`; context=2048; output cap=128; completion=5; finish=`stop`; answer=`2011`
- `long_context_retrieval`; context=2048; output cap=128; completion=5; finish=`stop`; answer=`2011`

### qwen3:1.7b
- `instruction_three_colors`; context=2048; output cap=128; completion=14; finish=`stop`; answer=````json ["red", "blue", "green"] ````
- `instruction_three_colors`; context=2048; output cap=128; completion=14; finish=`stop`; answer=````json ["red", "blue", "green"] ````

### qwen3:4b
- `ctx512_target128_out32`; context=512; output cap=32; completion=32; finish=`length`; answer=`We are given a passage that contains a marker assigned to a fictional research run. The instruction says: "Ignore all other words that resemble labels." and we are`
- `ctx512_target128_out32`; context=512; output cap=32; completion=32; finish=`length`; answer=`We are given a passage that contains a marker assigned to a fictional research run. The instruction says: "Ignore all other words that resemble labels." and we are`
- `ctx512_target128_out128`; context=512; output cap=128; completion=128; finish=`length`; answer=`We are given a passage that contains a marker assigned to a fictional research run. The instruction says: "Ignore all other words that resemble labels." and we are to return only t…`
- `ctx512_target128_out128`; context=512; output cap=128; completion=128; finish=`length`; answer=`We are given a passage that contains a marker assigned to a fictional research run. The instruction says: "Ignore all other words that resemble labels." and we are to return only t…`
- `ctx1024_target128_out32`; context=1024; output cap=32; completion=32; finish=`length`; answer=`We are given a passage that contains a marker assigned to a fictional research run. The instruction says: "Ignore all other words that resemble labels." and we are`

## Interpretation and limitations

- **Do not select a winner from speed alone.** Combine quality, latency, throughput, context fit, output-cap behavior, and failure rate.
- **Quality suite is a small diagnostic smoke test**, not a validated benchmark dataset; do not generalize its accuracy to domain performance.
- **Context fit** compares server-reported prompt tokens plus requested output cap with the requested context. Model/runtime implementations may differ.
- **Output caps are maximums**, not guaranteed generation lengths. A response ending at `length` likely exhausted its cap.
- **Quantization comparisons** should use the same model family/revision and matched prompts on the same hardware.
- **Memory caveat:** Ollama RSS/USS values are sampled after requests and may miss transient peaks; Python process memory is reported separately in raw results.

## Per-model notes

### qwen3:0.6b

- Model metadata: `{"family": "qwen3", "families": ["qwen3"], "parameter_size": "751.63M", "quantization": "Q4_K_M", "format": "gguf", "capabilities": ["completion", "tools", "thinking"], "metadata_error": null}`
- Runtime: `{"python": "3.11.17", "platform": "Linux-7.0.0-1017-azure-x86_64-with-glibc2.39", "cpu_count_logical": 4, "ram_total_gb": 15.61, "ram_available_gb_at_start": 12.11, "ollama_version": "ollama version is 0.40.8", "ollama_host": "http://127.0.0.1:11434"}`
- Results: 108 successful, 0 errors, 32 skipped
- Context-fit rate among checked matrix cases: 1.0
- Sentinel retrieval: 86/86 (1.0)
- Quality suite: 6/10 correct (0.6)
- Position retrieval: 6/6 correct (1.0)
- Output-cap probes reaching the requested cap: 4/6
- Successful records with empty final answer: 0
- Records with a separate/parsed thinking field: 0
- Max observed Ollama process RSS / USS after requests: None / None GiB

### qwen3:1.7b

- Model metadata: `{"family": "qwen3", "families": ["qwen3"], "parameter_size": "2.0B", "quantization": "Q4_K_M", "format": "gguf", "capabilities": ["completion", "tools", "thinking"], "metadata_error": null}`
- Runtime: `{"python": "3.11.17", "platform": "Linux-7.0.0-1017-azure-x86_64-with-glibc2.39", "cpu_count_logical": 4, "ram_total_gb": 15.61, "ram_available_gb_at_start": 8.77, "ollama_version": "ollama version is 0.40.8", "ollama_host": "http://127.0.0.1:11434"}`
- Results: 108 successful, 0 errors, 32 skipped
- Context-fit rate among checked matrix cases: 1.0
- Sentinel retrieval: 86/86 (1.0)
- Quality suite: 8/10 correct (0.8)
- Position retrieval: 6/6 correct (1.0)
- Output-cap probes reaching the requested cap: 6/6
- Successful records with empty final answer: 0
- Records with a separate/parsed thinking field: 0
- Max observed Ollama process RSS / USS after requests: None / None GiB

### qwen3:4b-q8_0

- Model metadata: `{"family": "qwen3", "families": ["qwen3"], "parameter_size": "4.0B", "quantization": "Q8_0", "format": "gguf", "capabilities": ["completion", "tools", "thinking"], "metadata_error": null}`
- Runtime: `{"python": "3.11.17", "platform": "Linux-7.0.0-1017-azure-x86_64-with-glibc2.39", "cpu_count_logical": 4, "ram_total_gb": 15.61, "ram_available_gb_at_start": 8.0, "ollama_version": "ollama version is 0.40.8", "ollama_host": "http://127.0.0.1:11434"}`
- Results: 108 successful, 0 errors, 32 skipped
- Context-fit rate among checked matrix cases: 1.0
- Sentinel retrieval: 86/86 (1.0)
- Quality suite: 10/10 correct (1.0)
- Position retrieval: 6/6 correct (1.0)
- Output-cap probes reaching the requested cap: 6/6
- Successful records with empty final answer: 0
- Records with a separate/parsed thinking field: 0
- Max observed Ollama process RSS / USS after requests: None / None GiB

### qwen3:4b

- Model metadata: `{"family": "qwen3", "families": ["qwen3"], "parameter_size": "4.0B", "quantization": "Q4_K_M", "format": "gguf", "capabilities": ["completion", "tools", "thinking"], "metadata_error": null}`
- Runtime: `{"python": "3.11.17", "platform": "Linux-7.0.0-1017-azure-x86_64-with-glibc2.39", "cpu_count_logical": 4, "ram_total_gb": 15.61, "ram_available_gb_at_start": 9.59, "ollama_version": "ollama version is 0.40.8", "ollama_host": "http://127.0.0.1:11434"}`
- Results: 108 successful, 0 errors, 32 skipped
- Context-fit rate among checked matrix cases: 1.0
- Sentinel retrieval: 0/86 (0.0)
- Quality suite: 4/10 correct (0.4)
- Position retrieval: 0/6 correct (0.0)
- Output-cap probes reaching the requested cap: 6/6
- Successful records with empty final answer: 0
- Records with a separate/parsed thinking field: 0
- Max observed Ollama process RSS / USS after requests: None / None GiB

## Case-level results

Full result rows, including answer text, timing, actual token counts, context checks, and error messages, are in `benchmark-summary.json`.

## Reproducibility

- Summary schema: `2`
- Raw per-model JSON files should be retained alongside this report.
- Re-run with the same runner type, model tags, Ollama version, context/input/output matrix, and repetition count to compare changes.
