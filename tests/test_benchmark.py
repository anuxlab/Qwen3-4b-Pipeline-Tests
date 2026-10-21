import json
from scripts.bench_ollama import make_prompt
from scripts.summarize_results import mean


def test_prompt_contains_answer_sentinel_and_question():
    prompt = make_prompt(128, "ORCHID")
    assert "ORCHID" in prompt
    assert "Question:" in prompt


def test_mean_ignores_missing_values():
    assert mean([1, 3, None, "bad"]) == 2.0
    assert mean([None]) is None


def test_summary_handles_empty_results(tmp_path):
    from scripts.summarize_results import main
    import sys
    src = tmp_path / "results"
    src.mkdir()
    (src / "sample.json").write_text(json.dumps({"method":"ollama", "model":"qwen3:test", "results":[]}))
    out_json, out_md = tmp_path / "summary.json", tmp_path / "summary.md"
    old = sys.argv
    try:
        sys.argv = ["summarize_results", "--input-dir", str(src), "--json-out", str(out_json), "--md-out", str(out_md)]
        main()
    finally:
        sys.argv = old
    data = json.loads(out_json.read_text())
    assert data["benchmark_runs"] == 1
    assert "Qwen End-to-End Benchmark Summary" in out_md.read_text()
