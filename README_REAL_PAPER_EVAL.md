# Real research-paper extraction evaluation

This workflow evaluates real open-access PDFs with Ollama models. The default is `qwen3:4b-q8_0`; alternatives can be selected from the GitHub Actions form. The repository includes five direct arXiv PDF links in `papers/urls.txt` so the workflow can run without manually uploading papers.

## Why this version uses task-specific extraction

The previous run downloaded and parsed all five PDFs successfully, but all five model responses failed with `JSONDecodeError: Unterminated string`. The request times were 154–180 seconds, so this was not the configured 300-second timeout. The most likely cause was that the model response was cut off while generating the full JSON object under a 1,024-token output cap.

This version changes the extraction contract:

1. **Metadata pass:** title, authors, year, DOI, abstract, and research problem only.
2. **Evidence passes:** each page-labelled chunk extracts only datasets, named models/algorithms, metrics/results, and claims with short exact quotes.
3. **Synthesis pass:** five-point summary, methodology, simulation, contributions, limitations, and future work.
4. **Bounded retry:** if a response is invalid or incomplete JSON, retry once with a larger token budget and stricter compact-output instructions.
5. **Merge and validate:** combine task outputs, validate against the final schema, and verify that evidence quotes occur on the cited page.

This avoids asking every chunk to regenerate all paper fields and large arrays. It cannot guarantee inference success on a hosted CPU runner, but it directly addresses the incomplete-JSON failure seen in the uploaded run.

## Recommended initial settings

- Model: `qwen3:4b-q8_0`
- Papers: `5`
- Context: `4096`
- Chunk size: `4000` characters
- Maximum generated tokens per request: `2048`
- Request timeout: `600` seconds
- Evidence judge: disabled

Start with five papers and inspect `paper-evaluation.json` before scaling to 10–20. Every evidence chunk prints progress to the Actions log. The report records per-task latency and token telemetry. The optional evidence-judge pass remains disabled because it adds more inference cost and is not ground truth.

## Included open-access sample cohort

`papers/urls.txt` lists direct PDF URLs from arXiv:

- Attention Is All You Need — https://arxiv.org/abs/1706.03762
- BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding — https://arxiv.org/abs/1810.04805
- Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks — https://arxiv.org/abs/2005.11401
- LoRA: Low-Rank Adaptation of Large Language Models — https://arxiv.org/abs/2106.09685
- Learning to Simulate: Generative Metamodeling via Quantile Regression — https://arxiv.org/abs/2311.17797

The URLs are downloaded to a temporary directory in the workflow. The PDFs are not committed to the repository. This five-paper cohort is a smoke test across different paper structures and content types, not a statistically representative accuracy benchmark.

## Run in GitHub Actions

1. Commit the updated codebase to your repository's default branch.
2. Open **Actions → Real research-paper extraction evaluation → Run workflow**.
3. Leave the model input at `qwen3:4b-q8_0` and the paper count at `5` for the first run.
4. Start with the defaults: `num_ctx=4096`, `max_chars=6000`, `num_predict=1024`, `request_timeout_sec=300`, and `judge_evidence=false`.
5. Download the `real-paper-extraction-eval-<run_id>` artifact after the run.

You can compare models by entering a comma-separated list, e.g. `qwen3:4b-q8_0,qwen3:1.7b,qwen3:0.6b`. The same paper cohort is used for each model.

## Local run

Requires Python 3.11+, Ollama, and the selected model pulled locally:

```bash
python -m pip install -r requirements-paper-eval.txt
ollama pull qwen3:4b-q8_0
ollama serve
```

In another terminal:

```bash
python scripts/paper_eval.py \
  --models qwen3:4b-q8_0 \
  --max-papers 5 \
  --max-chars 4000 \
  --num-ctx 4096 \
  --num-predict 2048 \
  --timeout 600 \
  --output-dir paper-eval-results
```

Add `--judge-evidence` to enable the optional second-pass model review. This is disabled by default to reduce timeout risk.

## Input choices

- Add your own PDFs directly to `papers/`, or replace the direct PDF links in `papers/urls.txt`.
- Keep the `max_papers` value between 1 and 20. For the supplied sample cohort, use 5.
- For URLs, use direct PDF endpoints rather than publisher landing pages. Download failures are reported and skipped.
- Scanned/image-only PDFs currently need OCR before evaluation; the pipeline flags them rather than pretending extraction succeeded.

## Output and interpretation

The uploaded artifact contains:

- `paper-evaluation.json`: full extracted fields, chunk telemetry, validation, evidence checks, timings, and optional gold scores.
- `PAPER_EVALUATION_REPORT.md`: per-model and per-paper summary.

The extractor returns bibliographic metadata, abstract, a five-point summary, research problem, contributions, datasets, model names, methodology, simulation presence/explanation, metrics/results, limitations, future work, and claims with page/quote evidence.

### What is and is not an accuracy score

- **JSON/schema validity** is deterministic.
- **Quote/page integrity** checks that a normalized quote appears on the page number claimed by the model. It does not prove the quote semantically supports the claim.
- **Model-judged support** is optional and must not be presented as ground truth.
- **DOI/title/year/author, dataset/model-name, and abstract accuracy** require gold annotations in `evaluation/gold/<pdf-stem>.json`. Without annotations, the run is a structural/provenance evaluation, not a definitive accuracy benchmark.
- **Cost** is an estimate. Local Ollama model-token cost is zero unless cost variables are set; runner cost is estimated from processing time and the configured hourly rate, not total GitHub job duration.

## Troubleshooting

- **Request timeout:** use `max_chars=3000`, `num_predict=2048`, and `num_ctx=4096`; the task-specific schema and compact retry are enabled by default. Avoid enabling the evidence judge until extraction succeeds.
- **Model pull / runner memory:** Q8 is memory-heavy for a hosted CPU runner. A persistent self-hosted Ollama endpoint may be more practical for repeated 5–20-paper runs.
- **No PDF inputs:** confirm `papers/urls.txt` is committed and contains direct PDF links or add PDFs under `papers/`.
- **No extractable text:** the PDF is likely scanned or text extraction is blocked; OCR is not currently bundled.
