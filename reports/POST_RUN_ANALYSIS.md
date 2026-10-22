# Post-run analysis: uploaded GitHub Actions benchmark

**Artifact reviewed:** `qwen-benchmark-39731227944.zip` and `logs_107675841715.zip`  
**Run timestamp:** 2026-10-22 UTC  
**Environment:** GitHub-hosted Ubuntu runner, 4 logical CPUs, ~15.6 GiB RAM, Ollama 0.40.8, CPU-only.

## Observed run totals

- 4 model tags; 560 result records.
- 432 successful HTTP/inference requests, 0 recorded request errors, and 128 budget-skipped matrix cases.
- 32 skipped cases per model are expected from the declared input + output + safety-margin budget rule. They are not inference failures.
- The report from this run had a very large Markdown file because it printed full Ollama Modelfile/template/license metadata. The updated summarizer now keeps the report metadata compact and retains full metadata only in raw per-model JSON.

## Results in the uploaded run

| Model tag | Quantization | Median latency | P95 latency | Median generation tok/s | Quality smoke score | Position retrieval | Matrix sentinel |
|---|---|---:|---:|---:|---:|---:|---:|
| `qwen3:0.6b` | Q4_K_M | 0.0965 s | 4.7122 s | 79.106 | 6/10 | 6/6 | 86/86 |
| `qwen3:1.7b` | Q4_K_M | 0.1523 s | 12.5079 s | 38.3675 | 8/10 | 6/6 | 86/86 |
| `qwen3:4b-q8_0` | Q8_0 | 0.5335 s | 47.9267 s | 10.4295 | 10/10 | 6/6 | 86/86 |
| `qwen3:4b` | Q4_K_M | 8.9319 s | 47.0271 s | 14.638 | 4/10 | 0/6 | 0/86 |

These are observations from the uploaded run, not guaranteed future results or a universal ranking. The quality suite has only five small task types, repeated twice.

## Critical finding: `qwen3:4b` Q4_K_M needs investigation

In this run, the `qwen3:4b` tag repeatedly returned text that paraphrased/repeated the prompt instead of the requested sentinel answer. The response often ended with `done_reason=length`, including at larger output caps. In contrast, `qwen3:4b-q8_0` returned the sentinel correctly in all 86 successful matrix cases.

This is too large a discrepancy to explain away as a small quantization trade-off. Before relying on the Q4 result:

1. Pull both tags again and record exact model digests.
2. Run the same one short sentinel prompt at `num_predict=128` and `512`, `num_ctx=2048`, with `think=false`.
3. Save the complete raw response fields and verify the model template/Modelfile for both tags.
4. Confirm the expected Qwen3 model artifact was pulled and no local custom model tag shadows the official tag.
5. Repeat the probe at least three times after the model is loaded; keep cold-load and warm-request latency separate.

Do not silently exclude the Q4 failures: retain them as observed failures unless the rerun establishes a reproducible setup/configuration issue.

## What was improved in this codebase

- Parses explicit `<think>...</think>` blocks and marks unfinished think-only responses as having no final answer.
- Stores raw content and thinking excerpts separately from the extracted final answer for diagnosis.
- Adds after-request Ollama process RSS/USS snapshots (best-effort; not a true transient peak measurement).
- Adds quality-by-task and sentinel accuracy broken down by requested context and output cap.
- Adds concise failure snippets to the report instead of dumping the complete model template.
- Keeps artifacts/report generation running after a model failure, then marks the workflow failed so errors cannot be hidden by a zero exit status.
- Adds offline regression tests for extraction, metadata compaction, statistics, and aggregation.

## Measurement caveats

- The hosted runner is CPU-only. These throughput and latency values are not GPU deployment estimates.
- Prompt targets are approximate. Ollama-reported prompt token counts are the observed values; the current prompt generator does not use a model-specific tokenizer.
- The recorded non-streaming time-to-first-token field is a proxy, not directly measured streaming TTFT.
- Memory snapshots occur after requests and can miss transient peaks.
- The built-in quality suite is a smoke test, not a research-grade evaluation set. Use a held-out dataset relevant to the intended task before choosing a winner.
