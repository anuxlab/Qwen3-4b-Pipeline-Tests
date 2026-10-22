# Benchmark scenario matrix and analysis guide

## Automated scenarios

| Scenario | What it tests | Evidence captured | How to interpret |
|---|---|---|---|
| Model setup | Pull availability and model metadata | Model tag, family, parameter size, quantization, setup errors | Missing tags are setup failures, not model-quality failures |
| Input × context × output matrix | Prompt prefill and generation under different budgets | Requested settings, actual prompt tokens, actual completion tokens, timing, context-fit flag | Compare matched cases; input target is approximate, not exact |
| Repeated trials | Timing variability | Wall latency and token throughput per repetition | Use medians/p95; don't infer small differences from one run |
| Sentinel retrieval | Basic response extraction and a simple known-answer task | Final answer text and exact-match flag | Only a pipeline smoke test; the answer is present in the prompt |
| Position retrieval | Needle at beginning, middle and end | Exact-match answer by position, actual prompt tokens | Detects a crude position effect; not a full long-context benchmark |
| Quality smoke suite | Short factual, reasoning, format and JSON tasks | Final answer, scoring method, expected answer, pass/fail | Tiny diagnostic suite; scores are noisy and not domain-general |
| Output-cap probe | Sustained generation at each configured cap | Requested cap, actual output count, finish reason, cap-hit indicator | A cap hit means the output was likely constrained; a short output is not automatically an error |
| Error handling | Timeouts, unavailable models, HTTP errors, bad responses | Per-case status and error message | Failures remain visible in the final report |

## Recommended staged run

1. **Smoke test:** one small model, two context values, two input targets, two output caps, one repetition, and three matrix cases maximum. Check answer text is non-empty and the report is generated.
2. **Calibration:** use one model to determine the approximate character/token relationship on this runtime; inspect `input_target_error_tokens` and adjust target settings if the prompts are consistently off target.
3. **Performance run:** same runner, all selected model/quantization tags, all planned context/input/output combinations, at least three repetitions if time permits.
4. **Quality/context run:** use position-sensitive retrieval and a larger, independently sourced task suite. Include beginning/middle/end and multiple needle distractors if context use is central to the research question.
5. **Replication:** rerun the best candidates on the same hardware, then on deployment-representative hardware. Do not compare CPU hosted runner results directly with GPU results.

## Selection framework

Avoid a single opaque aggregate score by default. First exclude configurations with setup failures, repeated inference errors, invalid context fit, or unacceptable quality. Then compare remaining candidates on:

- quality on task-specific, held-out data;
- median and p95 latency;
- generation tokens/second and prompt processing time;
- memory and model size, measured on the actual deployment host;
- maximum context tested with correct retrieval at multiple positions;
- output-cap behavior and reliability.

If an aggregate ranking is later required, define and publish the weights before evaluating the models. The built-in smoke-suite score should not be used as a final research ranking.

## Known limitations

- Input lengths use a character heuristic. The Ollama-reported prompt token count is the observed metric; a model-specific tokenizer is needed to target exact token lengths in advance.
- The non-streaming API only provides a time-to-first-token proxy (load plus prompt evaluation), not direct streamed TTFT.
- The built-in position test is a basic needle probe. It does not prove the model attended to every token or supports the claimed maximum context.
- Peak GPU memory is not available from this CPU-oriented generic runner. For deployment profiling, capture GPU VRAM and system RAM with platform-specific tooling.
- Model tags can change over time. Save model metadata and rerun tests after tag/runtime changes.
