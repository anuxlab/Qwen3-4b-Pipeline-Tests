# Hotfix: Incomplete JSON from Qwen3 4B Q8

## What the failed run showed
All five PDFs downloaded and parsed. Every model response then failed with `JSONDecodeError: Unterminated string` after roughly 154–180 seconds. This is consistent with incomplete structured output; it is not the configured 300-second request timeout.

## Changes
- Replaced the one-large-schema-per-chunk pattern with three task-specific extraction stages:
  1. bibliographic metadata and abstract,
  2. compact evidence extraction per page-labelled chunk,
  3. short paper synthesis.
- Added one bounded retry for invalid/incomplete JSON with a larger generation budget and compact-output instructions.
- Defaults changed to 4,000 characters per chunk, 2,048 generated tokens, 600 seconds per request.
- Workflow now checks whether the Ollama API is already available before starting another server process.
- Telemetry records each task and retry without creating circular JSON references.
- Added a mocked end-to-end test for the task-specific extraction path.

## Apply
Merge this add-on into the root of `anuxlab/Qwen3-4b-Pipeline-Tests`, commit and push, then rerun the workflow with five papers and `qwen3:4b-q8_0`.

## Validation
Offline tests: 23 passed. No live Ollama inference was run while preparing this patch; the next GitHub Actions run is required to confirm model extraction success.


## Reuse previously parsed paper text

The five papers are the same five arXiv URLs from the previous run. The uploaded failed-run artifact reports page counts and total text lengths, but does not include the extracted page text or the PDF files, so those exact parsed page records cannot be seeded from the artifact. This update adds a SHA-256 keyed text cache, reuses valid downloaded PDFs, caches both directories with `actions/cache`, and uploads the page-text cache as an artifact. The first run after this change will populate the cache; subsequent runs with unchanged papers will reuse it. Model extraction still needs to run because the previous run produced no valid extractions.
