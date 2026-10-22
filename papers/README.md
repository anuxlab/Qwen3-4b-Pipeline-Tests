# Research-paper evaluation inputs

The default `urls.txt` points to five openly accessible arXiv PDF endpoints for a smoke-test cohort spanning Transformer methods, language-model pre-training, RAG, parameter-efficient fine-tuning, and simulation/metamodeling. The workflow downloads them into a temporary directory; it does not commit PDF binaries back to this repository.

The first five are a smoke-test cohort, not a statistically representative accuracy benchmark. You can replace or extend the list with other openly accessible direct PDF links, one URL per line. Use `https://arxiv.org/pdf/<arXiv-ID>` for arXiv papers. To evaluate your own papers, add PDFs directly here or change `papers/urls.txt`.

For accuracy scores, add human-reviewed annotations at `evaluation/gold/<downloaded-pdf-stem>.json`. Without gold labels, the pipeline reports structural and evidence-provenance checks but does not claim scientific extraction accuracy.
