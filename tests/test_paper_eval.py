import json
from pathlib import Path
from scripts.paper_eval import validate_output, build_prompt, score_gold, SCHEMA


def base_output():
    return {
      "title":"Paper title", "authors":["A. Author"], "year":2024, "doi":None,
      "abstract":"Abstract text", "five_point_summary":["Point one"], "research_problem":"Problem",
      "contributions":[], "datasets":[{"name":"Dataset X","role":"test","evidence":{"page":1,"quote":"Dataset X was used."}}],
      "models":[], "methodology_explanation":"Method description", "simulation_explanation":None,
      "metrics_and_results":[], "limitations":[], "future_work":[], "simulation_present":False,
      "missing_fields":[], "claims":[{"claim":"The method uses Dataset X.","evidence":{"page":1,"quote":"Dataset X was used."}}]
    }


def test_quote_page_validation():
    pages=[{"page":1,"text":"Dataset X was used.\nThe method is described."},{"page":2,"text":"Results."}]
    result=validate_output(base_output(),pages)
    assert result['json_valid'] is True
    assert result['schema_valid'] is True
    assert result['evidence_checks']['quote_exact_on_page']==2


def test_wrong_page_or_quote_is_flagged():
    data=base_output(); data['datasets'][0]['evidence']={'page':2,'quote':'Dataset X was used.'}
    result=validate_output(data,[{"page":1,"text":"Dataset X was used."},{"page":2,"text":"Results."}])
    assert result['evidence_checks']['quote_not_found']==1


def test_missing_required_fields_detected():
    data=base_output(); del data['abstract']
    result=validate_output(data,[{"page":1,"text":"Dataset X was used."}])
    assert result['schema_valid'] is False
    assert 'abstract' in result['missing_required_fields']


def test_prompt_preserves_page_labels():
    pages=[{"page":1,"text":"A"*100},{"page":2,"text":"Methodology "*20}]
    prompt=build_prompt(pages,200)
    assert '[PDF PAGE' in prompt


def test_gold_scoring_datasets_and_models():
    result=score_gold(base_output(),{"datasets":["Dataset X"],"models":[],"year":2024})
    assert result['datasets']['f1']==1.0
    assert result['models']['f1']==1.0
    assert result['year']['match'] is True


def test_full_json_schema_validation():
    data=base_output()
    data['year']='2024'  # schema requires an integer or null
    result=validate_output(data,[{"page":1,"text":"Dataset X was used."}])
    assert result['json_valid'] is True
    assert result['schema_valid'] is False
    assert any('year' in error for error in result['schema_errors'])


def test_page_chunks_cover_all_pages_and_respect_budget():
    from scripts.paper_eval import build_page_chunks
    pages = [
        {"page": 1, "text": "Intro " * 300},
        {"page": 2, "text": "Methods " * 300},
        {"page": 3, "text": "Results " * 300},
    ]
    chunks = build_page_chunks(pages, 2500)
    joined = "\n".join(chunks)
    assert len(chunks) > 1
    assert "PDF PAGE 1" in joined and "PDF PAGE 2" in joined and "PDF PAGE 3" in joined
    assert all(len(chunk) <= 2500 for chunk in chunks)


def test_chunk_merge_preserves_distinct_evidence_and_simulation_flag():
    from scripts.paper_eval import merge_partial_extractions
    a = base_output()
    a["title"] = "A paper"
    a["simulation_present"] = False
    b = base_output()
    b["title"] = None
    b["simulation_present"] = True
    b["simulation_explanation"] = "The paper uses a discrete-event simulation."
    b["datasets"] = [{"name": "Dataset Y", "role": "test", "evidence": {"page": 3, "quote": "Dataset Y is evaluated."}}]
    merged = merge_partial_extractions([a, b])
    assert merged["title"] == "A paper"
    assert merged["simulation_present"] is True
    assert "Dataset X" in [x["name"] for x in merged["datasets"]]
    assert "Dataset Y" in [x["name"] for x in merged["datasets"]]
    assert merged["simulation_explanation"] == "The paper uses a discrete-event simulation."
