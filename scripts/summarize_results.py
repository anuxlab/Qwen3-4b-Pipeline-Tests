"""Create one consolidated Markdown + JSON report from per-model benchmark result files."""
from __future__ import annotations
import argparse, glob, json, math, os, statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def numeric(values):
    return [float(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))]

def stat(values, which="mean"):
    vals = numeric(values)
    if not vals: return None
    if which == "median": v = statistics.median(vals)
    elif which == "p95": v = sorted(vals)[min(len(vals)-1, math.ceil(.95*len(vals))-1)]
    else: v = statistics.mean(vals)
    return round(v, 4)

def load_runs(input_dir: str, json_out: str):
    paths = sorted(glob.glob(os.path.join(input_dir, "**", "*.json"), recursive=True))
    payloads = []
    out_abs = os.path.abspath(json_out)
    for path in paths:
        if os.path.abspath(path) == out_abs or os.path.basename(path) == "benchmark-summary.json": continue
        try:
            d = json.loads(Path(path).read_text(encoding="utf-8"))
            if isinstance(d, dict) and isinstance(d.get("results"), list) and d.get("model"):
                payloads.append((path, d))
        except (OSError, json.JSONDecodeError):
            continue
    return payloads, len(paths)

def summarize_run(path: str, d: dict[str, Any]) -> dict[str, Any]:
    allr = d.get("results", [])
    good = [r for r in allr if r.get("status", "ok") == "ok"]
    failed = [r for r in allr if r.get("status") == "error"]
    skipped = [r for r in allr if str(r.get("status", "")).startswith("skipped")]
    quality = [r for r in good if r.get("kind") == "quality" and isinstance(r.get("answer_correct"), bool)]
    position = [r for r in good if r.get("kind") == "position_retrieval" and isinstance(r.get("answer_correct"), bool)]
    cap_probes = [r for r in good if r.get("kind") == "output_cap_probe"]
    matrix = [r for r in good if r.get("kind") == "context_matrix"]
    def values(key, rows=good): return [r.get(key) for r in rows]
    return {"source_file":path, "method":d.get("method", "unknown"), "model":d.get("model", "unknown"),
      "parameter_size":(d.get("model_info") or {}).get("parameter_size"), "quantization":(d.get("model_info") or {}).get("quantization"),
      "model_info":d.get("model_info", {}), "runtime":d.get("runtime", {}), "test_plan":d.get("test_plan", {}),
      "records":len(allr), "successes":len(good), "failures":len(failed), "skipped":len(skipped),
      "success_rate":round(len(good)/len(allr),4) if allr else None,
      "latency_mean_sec":stat(values("wall_latency_sec")), "latency_median_sec":stat(values("wall_latency_sec"),"median"),
      "latency_p95_sec":stat(values("wall_latency_sec"),"p95"), "generation_tps_mean":stat(values("generation_tokens_per_sec")),
      "generation_tps_median":stat(values("generation_tokens_per_sec"),"median"),
      "prompt_eval_mean_sec":stat(values("prompt_eval_sec")), "load_mean_sec":stat(values("load_sec")),
      "mean_actual_prompt_tokens":stat(values("prompt_tokens_actual")), "mean_actual_completion_tokens":stat(values("completion_tokens_actual")),
      "context_fit_count":sum(r.get("context_fit") is True for r in matrix), "context_fit_checked":sum(isinstance(r.get("context_fit"),bool) for r in matrix),
      "sentinel_accuracy":round(sum(r.get("sentinel_answer_correct") is True for r in matrix)/len(matrix),4) if matrix else None,
      "quality_correct":sum(r.get("answer_correct") is True for r in quality), "quality_cases_scored":len(quality),
      "quality_accuracy":round(sum(r.get("answer_correct") is True for r in quality)/len(quality),4) if quality else None,
      "position_retrieval_correct":sum(r.get("answer_correct") is True for r in position), "position_retrieval_scored":len(position),
      "position_retrieval_accuracy":round(sum(r.get("answer_correct") is True for r in position)/len(position),4) if position else None,
      "output_cap_probes":len(cap_probes), "output_cap_respected":sum(r.get("output_cap_respected") is True for r in cap_probes),
      "output_cap_likely_limited":sum(r.get("likely_cap_limited") is True for r in cap_probes),
      "results":allr}

def md_table(rows, keys, headers):
    out=["| " + " | ".join(headers) + " |", "|"+"|".join(["---"]*len(headers))+"|"]
    for row in rows:
        out.append("| " + " | ".join("—" if row.get(k) is None else str(row.get(k)) for k in keys) + " |")
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir",default="results")
    ap.add_argument("--json-out",default="benchmark-summary.json")
    ap.add_argument("--md-out",default="BENCHMARK_SUMMARY.md")
    args=ap.parse_args()
    payloads, discovered=load_runs(args.input_dir,args.json_out)
    runs=[summarize_run(p,d) for p,d in payloads]
    records=[x for r in runs for x in r["results"]]
    summary={"schema_version":2,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"files_discovered":discovered,
      "benchmark_runs":len(runs),"overall":{"records":len(records),"successes":sum(r["successes"] for r in runs),
      "failures":sum(r["failures"] for r in runs),"skipped":sum(r["skipped"] for r in runs)},"runs":runs}
    Path(args.json_out).parent.mkdir(parents=True,exist_ok=True)
    Path(args.json_out).write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["# Qwen End-to-End Benchmark Report","",f"Generated UTC: {summary['generated_at_utc']}","",
      "> Important: a successful HTTP request is not proof of useful model quality. Input targets are heuristic; `prompt_tokens_actual` is the server-reported prompt count. Compare models only on matched hardware, model revisions, context, prompts, and repetitions.","",
      "## Executive summary","",f"- Model runs: **{summary['benchmark_runs']}**",f"- Result records: **{summary['overall']['records']}**",f"- Successful: **{summary['overall']['successes']}**",f"- Errors: **{summary['overall']['failures']}**",f"- Skipped due to budget: **{summary['overall']['skipped']}**","",
      "## Configuration comparison","",*md_table(runs,["model","parameter_size","quantization","successes","failures","latency_median_sec","latency_p95_sec","generation_tps_median","quality_accuracy","position_retrieval_accuracy","sentinel_accuracy"],["Model","Params","Quant","OK","Errors","Median latency s","P95 latency s","Median tok/s","Quality accuracy","Position retrieval","Sentinel accuracy"]),"",
      "## Interpretation and limitations","",
      "- **Do not select a winner from speed alone.** Use the quality suite, latency, throughput, context-fit checks, and failure rate together.",
      "- **Quality suite is a small smoke test**, not a validated benchmark dataset. Its accuracy should not be generalized to domain performance.",
      "- **Context-fit** checks compare server-reported prompt tokens plus requested output cap against the requested context setting; actual runtime behavior can still depend on Ollama/model implementation.",
      "- **Output caps are maximums**, not guaranteed output lengths. `output_cap_reached` is reported separately.",
      "- **Quantization** is taken from Ollama metadata where available. Compare quantization only for the same model family/revision and comparable prompt cases.","",
      "## Per-model notes",""]
    for r in runs:
        lines += [f"### {r['model']}","",f"- Model metadata: `{json.dumps(r['model_info'],ensure_ascii=False)}`",f"- Runtime: `{json.dumps(r['runtime'],ensure_ascii=False)}`",f"- Results: {r['successes']} successful, {r['failures']} errors, {r['skipped']} skipped",f"- Quality suite: {r['quality_correct']}/{r['quality_cases_scored']} correct ({r['quality_accuracy'] if r['quality_accuracy'] is not None else 'not scored'})",""]
        errs=[x for x in r["results"] if x.get("status")=="error"]
        if errs:
            lines += ["Errors:", *[f"- `{e.get('case_id','unknown')}`: {e.get('error','unspecified error')}" for e in errs[:30]],""]
    lines += ["## Case-level results","","Full result rows, including answer text, timing, actual token counts, context checks, and error messages, are in `benchmark-summary.json`.","","## Reproducibility","",f"- Summary schema: `{summary['schema_version']}`", "- Raw per-model JSON files should be retained alongside this report.", "- Re-run with the same runner type, model tags, Ollama version, context/input/output matrix, and repetition count to compare changes."]
    Path(args.md_out).write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"Wrote {args.json_out} and {args.md_out}: {len(runs)} model runs, {summary['overall']['records']} records")
if __name__=="__main__": main()
