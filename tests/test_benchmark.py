import json
from scripts.bench_ollama import extract_answer, make_long_context_prompt, parse_ints, quality_cases, score_quality
from scripts.summarize_results import summarize_run, stat


def test_prompt_has_marker_and_question():
    p = make_long_context_prompt(256)
    assert "ORCHID" in p and "Question:" in p
    assert len(p) > 500


def test_extract_answer_chat_and_legacy():
    assert extract_answer({"message":{"content":"Paris","thinking":"hmm"}}) == ("Paris", "hmm")
    assert extract_answer({"response":"Paris"}) == ("Paris", None)


def test_extract_answer_removes_embedded_think_block():
    answer, thinking = extract_answer({"message":{"content":"Let me reason. <think>hidden thought</think>\nParis"}})
    assert answer == "Paris"
    assert "hidden thought" in thinking


def test_extract_answer_does_not_score_unfinished_think_block():
    answer, thinking = extract_answer({"message":{"content":"<think>unfinished reasoning"}})
    assert answer == ""
    assert "unfinished reasoning" in thinking


def test_parse_ints_deduplicates_and_sorts():
    assert parse_ints("1024,512,512", "contexts") == [512,1024]


def test_quality_exact_match_and_json():
    cases = {c["id"]: c for c in quality_cases()}
    assert score_quality(cases["qa_capital_france"], "Paris.")[0]
    assert score_quality(cases["structured_json"], '{"status":"ok","count":3}')[0]
    assert not score_quality(cases["structured_json"], "not json")[0]


def test_stat_percentiles_and_missing():
    assert stat([1, 2, 3]) == 2.0
    assert stat([1, 2, 3], "median") == 2.0
    assert stat([1, 2, 3, 4], "p95") == 4.0
    assert stat([None, "bad"]) is None


def test_summary_counts_quality_and_context():
    d={"model":"qwen:test","method":"ollama_chat","model_info":{"quantization":"Q4_K_M"},"results":[
      {"status":"ok","kind":"context_matrix","wall_latency_sec":2,"generation_tokens_per_sec":10,"context_fit":True,"sentinel_answer_correct":True},
      {"status":"ok","kind":"quality","wall_latency_sec":3,"generation_tokens_per_sec":8,"answer_correct":True},
      {"status":"error","kind":"quality","error":"timeout"},
      {"status":"skipped_budget","kind":"context_matrix"}]}
    r=summarize_run("fake.json",d)
    assert r["successes"] == 2 and r["failures"] == 1 and r["skipped"] == 1
    assert r["quality_accuracy"] == 1.0 and r["context_fit_count"] == 1


def test_json_serializable_answer_fields():
    result={"answer_text":"Paris","thinking_present":False,"context_fit":True}
    assert json.loads(json.dumps(result))["answer_text"] == "Paris"


def test_position_prompt_places_needle_and_returns_expected():
    from scripts.bench_ollama import make_position_prompt
    for pos in ("beginning", "middle", "end"):
        prompt, expected = make_position_prompt(256, pos)
        assert expected == "X7-ORCHID-29"
        assert prompt.count(expected) == 1
        assert "Question:" in prompt


def test_budget_skip_is_not_counted_as_success():
    from scripts.summarize_results import summarize_run
    r = summarize_run("x.json", {"model":"x", "results":[{"status":"skipped_budget"}]})
    assert r["successes"] == 0 and r["skipped"] == 1 and r["failures"] == 0





def test_summary_compacts_model_metadata():
    d = {"model": "qwen:test", "model_info": {
        "family": "qwen3", "quantization": "Q4_K_M",
        "modelfile": "very long modelfile", "template": "very long template",
        "parameter_size": "4B"
    }, "results": []}
    result = summarize_run("x.json", d)
    assert result["model_info"] == {
        "family": "qwen3", "quantization": "Q4_K_M", "parameter_size": "4B"
    }


def test_summary_memory_max_stat():
    assert stat([0.2, 0.7, 0.5], "max") == 0.7


def test_build_matrix_creates_one_entry_per_unique_model_and_safe_names():
    from scripts.build_matrix import build_matrix
    matrix = build_matrix('qwen3:0.6b, qwen3:4b, qwen3:0.6b, qwen3:4b-q8_0')
    entries = matrix['include']
    assert [x['model'] for x in entries] == ['qwen3:0.6b', 'qwen3:4b', 'qwen3:4b-q8_0']
    assert len({x['safe_name'] for x in entries}) == len(entries)
    assert all('/' not in x['safe_name'] and ':' not in x['safe_name'] for x in entries)

def test_build_matrix_rejects_empty_model_list():
    import pytest
    from scripts.build_matrix import build_matrix
    with pytest.raises(ValueError):
        build_matrix(' , , ')
