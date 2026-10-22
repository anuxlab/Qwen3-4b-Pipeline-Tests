# Real research-paper extraction evaluation

This is an additive workflow; it does not replace the synthetic Qwen context benchmark.

## Run it

1. Add 5–20 research PDFs to `papers/`, **or** create `papers/urls.txt` with one direct PDF URL per line. Use accessible PDFs that you are authorized to process.
2. Optional but strongly recommended: add manually checked gold annotations under `evaluation/gold/<pdf-stem>.json` to score metadata, dataset names, and model names. See `evaluation/gold/README.md`.
3. Push the files to GitHub.
4. Open **Actions → Real research-paper extraction evaluation → Run workflow**.
5. Default model is `qwen3:4b-q8_0`. To test multiple models, enter comma-separated Ollama tags, e.g. `qwen3:4b-q8_0,qwen3:1.7b,qwen3:0.6b`. The chosen model(s) are run against the same papers.
6. Choose 5, 10, 15, or 20 PDFs, context, and maximum source characters. Download the `real-paper-extraction-eval-<run_id>` artifact.

## What is extracted

- DOI, title, authors, year and abstract
- Five-point short summary
- Research problem and contributions
- Dataset and model names with roles and page-level evidence quotes
- Methodology explanation
- Simulation explanation, with a flag for whether simulation appears to be present
- Metrics/results, limitations, future work, and other evidence-backed claims

## What is measured

- JSON parse success and required-key/schema checks
- Missing/empty core fields
- Evidence quote existence on the cited page (whitespace-normalized exact match)
- A second-pass model-assisted support judgement against the full cited page (`supported`, `partially_supported`, `unsupported`, `unclear`)
- Page count, extraction coverage, latency, token counts/throughput when Ollama reports them
- Estimated token and runner cost, using optional workflow inputs/repository variables
- Gold-set DOI/title/year exact matches and dataset/model precision, recall, and F1 when annotations exist

**Accuracy caveat:** without gold annotations, metadata and entity extraction accuracy cannot be honestly calculated. The DOI regex is a candidate detector, not a gold label. Quote/page matching proves the quote exists on that page, not that it semantically entails the claim. The second-pass support verdict is also model-generated and may be wrong; manually review high-impact claims and a sample of all verdicts. Review `evidence_items` and `evidence_judgement` in the JSON and annotate a subset of papers for semantic correctness.

## Input and runtime details

- `papers/` accepts PDFs committed to the repo. `papers/urls.txt` accepts direct HTTP(S) PDF URLs. URL downloads happen in the runner and are not committed.
- The parser uses PyMuPDF. Scanned/image-only PDFs are flagged if no text is extracted; OCR is not automatically performed in this first version.
- Ollama receives page-labelled text with a configurable character budget. If the paper is longer than the budget, pages are selected by a simple abstract/method/results/simulation/conclusion heuristic; the report makes the budget explicit. For rigorous production use, evaluate chunked multi-pass extraction next.
- Cost defaults to zero for model token pricing because local Ollama does not bill per token. Set repository variables `INPUT_COST_PER_MILLION`, `OUTPUT_COST_PER_MILLION`, and the workflow's `runner_cost_per_hour` input if you want an estimate. Runner cost here is only proportional to model inference time, not total billable workflow time.
- The model can produce unsupported claims. JSON schema and evidence checks reduce structural/provenance errors but are not a replacement for human verification.

## Run locally

```bash
pip install -r requirements-paper-eval.txt
ollama serve  # in another terminal, if not already running
ollama pull qwen3:4b-q8_0
python scripts/paper_eval.py --models qwen3:4b-q8_0 --max-papers 5
pytest -q
```

Set `OLLAMA_BASE_URL` if Ollama is not on `http://127.0.0.1:11434`.
