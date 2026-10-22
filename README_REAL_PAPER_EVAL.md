# Real research-paper extraction evaluation

This workflow evaluates real open-access PDFs with Ollama models. The default is `qwen3:4b-q8_0`; alternatives can be selected from the GitHub Actions form. The repository includes five direct arXiv PDF links in `papers/urls.txt` so the workflow can run without manually uploading papers.

## Why this version uses chunked extraction

The previous flow sent a large portion of an entire PDF in one request and then ran a second model-judge request. On CPU GitHub-hosted runners, that caused requests to hit the 600-second timeout. This version:

1. Parses all PDF pages with `pymupdf` (no deprecated `fitz` import).
2. Preserves one-based PDF page labels and splits the paper into bounded chunks (default 6,000 characters per request).
3. Makes a separate constrained-JSON extraction request for each chunk, with a 4,096-token context and 1,024-token generation cap by default.
4. Merges extracted fields and deduplicates list items while preserving each item's page-level evidence.
5. Validates the merged result against JSON Schema and checks whether each evidence quote occurs on the claimed page.
6. Skips the extra model-based evidence judge by default. It can be enabled from the workflow input, but it costs more time and is only a screening signal.

This reduces the size of each request and makes progress visible per chunk. It cannot guarantee that every model call will finish within the timeout; if a call fails, reduce the chunk size to 4,000 characters or use a faster/persistent inference host.

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
  --max-chars 6000 \
  --num-ctx 4096 \
  --num-predict 1024 \
  --timeout 300 \
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

- **Request timeout:** retry with `max_chars=4000`, `num_predict=512` or `1024`, and `num_ctx=4096`. Avoid enabling the evidence judge until extraction succeeds.
- **Model pull / runner memory:** Q8 is memory-heavy for a hosted CPU runner. A persistent self-hosted Ollama endpoint may be more practical for repeated 5–20-paper runs.
- **No PDF inputs:** confirm `papers/urls.txt` is committed and contains direct PDF links or add PDFs under `papers/`.
- **No extractable text:** the PDF is likely scanned or text extraction is blocked; OCR is not currently bundled.
