# Optional gold annotations

Create one JSON file per PDF, named after the PDF stem, to measure field-level accuracy. Example:

```json
{
  "doi": "10.1234/example.2025.01",
  "title": "Example title",
  "year": 2025,
  "authors": ["A. Author", "B. Author"],
  "abstract": "A manually verified abstract text from the paper.",
  "datasets": ["Dataset A", "Dataset B"],
  "models": ["Model X"]
}
```

Fields are optional. DOI/title/year/authors are scored as exact normalized matches; abstract is scored with token-level precision/recall/F1; dataset/model names use set-based precision/recall/F1. Gold metadata is used only for scoring and is not sent to the model. Use the exact PDF filename stem, e.g. `paper-1.pdf` -> `paper-1.json`. Gold annotations should be checked by a human against the paper.
