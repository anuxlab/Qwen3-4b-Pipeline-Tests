# Research PDFs for the real-paper evaluation

Place 5–20 research-paper PDFs in this directory. The workflow uses these files by default.

Optional: add `urls.txt` with one direct PDF URL per line (blank lines and `#` comments are ignored). URLs are downloaded into the workflow's temporary workspace; they are not committed back to the repository. Use papers you are authorized to download and process. Publisher sites may block automated downloads.

For a meaningful accuracy score, create optional annotations in `evaluation/gold/<pdf-stem>.json` (see `evaluation/gold/README.md`). Without gold annotations, the report can measure structural validity, extraction coverage, timing, and evidence-quote/page integrity, but cannot truthfully calculate extraction accuracy.
