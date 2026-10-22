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
    elif which == "max": v = max(vals)
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

def compact_model_info(info: dict[str, Any]) -> dict[str, Any]:
    """Keep report metadata useful and avoid embedding full Modelfile/template/license."""
    keep = ("family", "families", "parameter_size", "quantization", "format",
            "capabilities", "metadata_error", "model_digest", "modified_at")
    return {k: info[k] for k in keep if k in info}


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
      "model_info":compact_model_info(d.get("model_info", {})), "runtime":d.get("runtime", {}), "test_plan":d.get("test_plan", {}),
      "records":len(allr), "successes":len(good), "failures":len(failed), "skipped":len(skipped),
      "success_rate":round(len(good)/len(allr),4) if allr else None,
      "latency_mean_sec":stat(values("wall_latency_sec")), "latency_median_sec":stat(values("wall_latency_sec"),"median"),
      "latency_p95_sec":stat(values("wall_latency_sec"),"p95"), "generation_tps_mean":stat(values("generation_tokens_per_sec")),
      "generation_tps_median":stat(values("generation_tokens_per_sec"),"median"),
      "prompt_eval_mean_sec":stat(values("prompt_eval_sec")), "load_mean_sec":stat(values("load_sec")),
      "ollama_process_rss_gb_max_observed":stat(values("ollama_process_rss_gb"), "max"),
      "ollama_process_uss_gb_max_observed":stat(values("ollama_process_uss_gb"), "max"),
      "mean_actual_prompt_tokens":stat(values("prompt_tokens_actual")), "mean_actual_completion_tokens":stat(values("completion_tokens_actual")),
      "context_fit_count":sum(r.get("context_fit") is True for r in matrix), "context_fit_checked":sum(isinstance(r.get("context_fit"),bool) for r in matrix),
      "sentinel_accuracy":round(sum(r.get("sentinel_answer_correct") is True for r in matrix)/len(matrix),4) if matrix else None,
      "sentinel_scored":sum(isinstance(r.get("sentinel_answer_correct"), bool) for r in matrix),
      "sentinel_correct":sum(r.get("sentinel_answer_correct") is True for r in matrix),
      "context_fit_rate":round(sum(r.get("context_fit") is True for r in matrix)/sum(isinstance(r.get("context_fit"), bool) for r in matrix),4) if any(isinstance(r.get("context_fit"), bool) for r in matrix) else None,
      "output_cap_reached_count":sum(r.get("output_cap_reached") is True for r in good),
      "empty_final_answer_count":sum(not str(r.get("answer_text") or "").strip() for r in good),
      "thinking_present_count":sum(r.get("thinking_present") is True for r in good),
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
      "> A successful HTTP request is not proof of useful model quality. Input targets are heuristic; prompt token counts are server-reported. Compare models only on matched hardware, model revisions, prompts, context, and repetitions.","",
      "## Executive summary","",f"- Model runs: **{summary['benchmark_runs']}**",f"- Result records: **{summary['overall']['records']}**",f"- Successful requests: **{summary['overall']['successes']}**",f"- Errors: **{summary['overall']['failures']}**",f"- Skipped cases: **{summary['overall']['skipped']}**","",
      "## Configuration comparison","",*md_table(runs,["model","parameter_size","quantization","successes","failures","latency_median_sec","latency_p95_sec","generation_tps_median","quality_accuracy","position_retrieval_accuracy","sentinel_accuracy"],["Model","Params","Quant","OK","Errors","Median latency s","P95 latency s","Median tok/s","Quality accuracy","Position retrieval","Sentinel accuracy"]),"",
      "## Sentinel retrieval by context and output cap","",
      "A short output cap can be exhausted by reasoning before a final answer is emitted. Read these scores alongside completion length and finish reason.","",
      "| Model | Context | Output cap | Correct / scored | Accuracy |", "|---|---:|---:|---:|---:|"]
    for run in runs:
        matrix_rows = [x for x in run["results"] if x.get("status") == "ok" and x.get("kind") == "context_matrix"]
        groups = {}
        for item in matrix_rows:
            key = (item.get("context_requested"), item.get("output_limit_requested"))
            groups.setdefault(key, []).append(item)
        for (ctx, cap), items in sorted(groups.items(), key=lambda pair: (pair[0][0] or 0, pair[0][1] or 0)):
            scored = [x for x in items if isinstance(x.get("sentinel_answer_correct"), bool)]
            correct = sum(x.get("sentinel_answer_correct") is True for x in scored)
            acc = round(correct / len(scored), 3) if scored else None
            lines.append(f"| {run['model']} | {ctx if ctx is not None else '—'} | {cap if cap is not None else '—'} | {correct}/{len(scored)} | {acc if acc is not None else 'not scored'} |")
    lines += ["", "## Quality suite by task", "",
      "| Model | Task | Correct / scored | Accuracy |", "|---|---|---:|---:|"]
    for run in runs:
        quality_rows = [x for x in run["results"] if x.get("status") == "ok" and x.get("kind") == "quality" and isinstance(x.get("answer_correct"), bool)]
        groups = {}
        for item in quality_rows:
            groups.setdefault(item.get("case_id", "unknown"), []).append(item)
        for case_id, items in sorted(groups.items()):
            correct = sum(x.get("answer_correct") is True for x in items)
            lines.append(f"| {run['model']} | {case_id} | {correct}/{len(items)} | {round(correct / len(items), 3) if items else 'not scored'} |")
    lines += ["", "## Failure diagnostics", "",
      "Examples below are diagnostic snippets, not a qualitative human evaluation. Inspect raw JSON for full answers.",""]
    flagged = 0
    for run in runs:
        failures = [x for x in run["results"] if x.get("status") == "ok" and (
            (x.get("kind") == "context_matrix" and x.get("sentinel_answer_correct") is False) or
            (x.get("kind") in ("quality", "position_retrieval") and x.get("answer_correct") is False))]
        if failures:
            lines.append(f"### {run['model']}")
            for item in failures[:5]:
                excerpt = str(item.get("answer_text") or item.get("response_excerpt") or item.get("raw_content_excerpt") or "").replace("\\n", " ").replace("\n", " ").replace("|", "\\|")
                excerpt = excerpt[:180] + ("…" if len(excerpt) > 180 else "")
                lines.append(f"- `{item.get('case_id', 'unknown')}`; context={item.get('context_requested')}; output cap={item.get('output_limit_requested')}; completion={item.get('completion_tokens_actual')}; finish=`{item.get('done_reason')}`; answer=`{excerpt}`")
                flagged += 1
            lines.append("")
    if not flagged:
        lines += ["No scored incorrect cases were recorded.",""]
    lines += ["## Interpretation and limitations","",
      "- **Do not select a winner from speed alone.** Combine quality, latency, throughput, context fit, output-cap behavior, and failure rate.",
      "- **Quality suite is a small diagnostic smoke test**, not a validated benchmark dataset; do not generalize its accuracy to domain performance.",
      "- **Context fit** compares server-reported prompt tokens plus requested output cap with the requested context. Model/runtime implementations may differ.",
      "- **Output caps are maximums**, not guaranteed generation lengths. A response ending at `length` likely exhausted its cap.",
      "- **Quantization comparisons** should use the same model family/revision and matched prompts on the same hardware.",
      "- **Memory caveat:** Ollama RSS/USS values are sampled after requests and may miss transient peaks; Python process memory is reported separately in raw results.","",
      "## Per-model notes",""]
    for r in runs:
        lines += [f"### {r['model']}","",f"- Model metadata: `{json.dumps(r['model_info'],ensure_ascii=False)}`",f"- Runtime: `{json.dumps(r['runtime'],ensure_ascii=False)}`",f"- Results: {r['successes']} successful, {r['failures']} errors, {r['skipped']} skipped",f"- Context-fit rate among checked matrix cases: {r['context_fit_rate'] if r['context_fit_rate'] is not None else 'not checked'}",f"- Sentinel retrieval: {r['sentinel_correct']}/{r['sentinel_scored']} ({r['sentinel_accuracy'] if r['sentinel_accuracy'] is not None else 'not scored'})",f"- Quality suite: {r['quality_correct']}/{r['quality_cases_scored']} correct ({r['quality_accuracy'] if r['quality_accuracy'] is not None else 'not scored'})",f"- Position retrieval: {r['position_retrieval_correct']}/{r['position_retrieval_scored']} correct ({r['position_retrieval_accuracy'] if r['position_retrieval_accuracy'] is not None else 'not scored'})",f"- Output-cap probes reaching the requested cap: {r['output_cap_likely_limited']}/{r['output_cap_probes']}",f"- Successful records with empty final answer: {r['empty_final_answer_count']}",f"- Records with a separate/parsed thinking field: {r['thinking_present_count']}",f"- Max observed Ollama process RSS / USS after requests: {r['ollama_process_rss_gb_max_observed']} / {r['ollama_process_uss_gb_max_observed']} GiB",""]
        errs=[x for x in r["results"] if x.get("status")=="error"]
        if errs:
            lines += ["Errors:", *[f"- `{e.get('case_id','unknown')}`: {e.get('error','unspecified error')}" for e in errs[:30]],""]
    lines += ["## Case-level results","","Full result rows, including answer text, timing, actual token counts, context checks, and error messages, are in `benchmark-summary.json`.","","## Reproducibility","",f"- Summary schema: `{summary['schema_version']}`", "- Raw per-model JSON files should be retained alongside this report.", "- Re-run with the same runner type, model tags, Ollama version, context/input/output matrix, and repetition count to compare changes."]
    Path(args.md_out).write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"Wrote {args.json_out} and {args.md_out}: {len(runs)} model runs, {summary['overall']['records']} records")
if __name__=="__main__": main()
