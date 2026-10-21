"""Merge benchmark JSON files into one machine-readable summary and a Markdown report."""
import argparse, glob, json, os, statistics
from datetime import datetime, timezone


def mean(values):
    vals = [float(v) for v in values if isinstance(v, (int, float))]
    return round(statistics.mean(vals), 3) if vals else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="results")
    ap.add_argument("--json-out", default="benchmark-summary.json")
    ap.add_argument("--md-out", default="BENCHMARK_SUMMARY.md")
    args = ap.parse_args()
    files = sorted(glob.glob(os.path.join(args.input_dir, "**", "*.json"), recursive=True))
    payloads = []
    for path in files:
        if os.path.abspath(path) in {os.path.abspath(args.json_out)}: continue
        try:
            with open(path, encoding="utf-8") as f: d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("results"), list): payloads.append((path, d))
        except (OSError, json.JSONDecodeError): pass
    rows = []
    for path, d in payloads:
        allr = d.get("results", [])
        good = [r for r in allr if r.get("status", "ok") == "ok"]
        rows.append({"source_file": path, "method": d.get("method", "unknown"), "model": d.get("model", "unknown"),
            "parameter_size": (d.get("model_info") or {}).get("parameter_size"),
            "quantization": (d.get("model_info") or {}).get("quantization"),
            "cases": len(allr), "successes": len(good), "failures": len(allr)-len(good),
            "success_rate": round(len(good)/len(allr), 3) if allr else 0,
            "mean_latency_sec": mean(r.get("latency_sec") for r in good),
            "mean_tokens_per_sec": mean(r.get("tokens_per_sec") for r in good),
            "mean_prompt_eval_sec": mean(r.get("prompt_eval_sec") for r in good),
            "mean_completion_tokens": mean(r.get("completion_tokens") for r in good),
            "mean_input_context_utilization": mean(r.get("input_context_utilization") for r in good),
            "answer_accuracy": round(sum(bool(r.get("answer_correct")) for r in good)/len(good), 3) if good and any("answer_correct" in r for r in good) else None,
            "model_info": d.get("model_info"), "runtime": d.get("runtime"), "test_plan": d.get("test_plan"),
            "results": allr})
    summary = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "files_discovered": len(files), "benchmark_runs": len(rows), "runs": rows,
               "overall": {"cases": sum(r["cases"] for r in rows), "successes": sum(r["successes"] for r in rows),
                           "failures": sum(r["failures"] for r in rows)}}
    with open(args.json_out, "w", encoding="utf-8") as f: json.dump(summary, f, indent=2)
    lines = ["# Qwen End-to-End Benchmark Summary", "", f"Generated (UTC): {summary['generated_at_utc']}",
             "", "> Compare results only when runner hardware, runtime, prompt suite, and model revisions are comparable. Context and output settings are requested limits; actual token counts are reported separately.", "",
             "## Overall", "", f"- Benchmark runs: **{summary['benchmark_runs']}**", f"- Cases: **{summary['overall']['cases']}**",
             f"- Successful cases: **{summary['overall']['successes']}**", f"- Failed cases: **{summary['overall']['failures']}**", "",
             "## Model / quantization comparison", "", "| Runtime | Model | Parameters | Quantization | Success | Mean latency (s) | Mean tok/s | Mean prompt eval (s) | Answer accuracy |", "|---|---|---:|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        lines.append(f"| {r['method']} | {r['model']} | {r['parameter_size'] or '—'} | {r['quantization'] or 'unknown'} | {r['successes']}/{r['cases']} | {r['mean_latency_sec'] if r['mean_latency_sec'] is not None else '—'} | {r['mean_tokens_per_sec'] if r['mean_tokens_per_sec'] is not None else '—'} | {r['mean_prompt_eval_sec'] if r['mean_prompt_eval_sec'] is not None else '—'} | {r['answer_accuracy'] if r['answer_accuracy'] is not None else '—'} |")
    lines += ["", "## Interpretation checklist", "", "- **Best quality:** compare answer accuracy and failure rate at matched input/context/output settings.", "- **Best throughput:** compare mean generated tokens/second; do not use latency alone for different output lengths.", "- **Best long-context behavior:** inspect cases at the largest context and actual `prompt_tokens`; reject cases where the prompt was truncated or did not fit.", "- **Output-limit behavior:** compare `completion_tokens`, `done_reason`, and `output_limit_reached` against each requested cap.", "- **Quantization trade-off:** compare quality, speed, memory, and load time for the same base model and runner.", "- **Limitations:** results depend on CPU/GPU, RAM, model tag/revision, Ollama version, and concurrency. This report does not infer unsupported context limits from a model label.", "", "## Case-level details", ""]
    for r in rows:
        lines += [f"### {r['model']} ({r['method']})", "", f"Source: `{r['source_file']}`", "", "| Case | Context | Target input | Actual input | Output cap | Generated | Latency s | tok/s | Status |", "|---|---:|---:|---:|---:|---:|---:|---:|---|"]
        for c in r["results"]:
            lines.append(f"| {c.get('case_id','—')} | {c.get('n_ctx','—')} | {c.get('target_input_tokens','—')} | {c.get('prompt_tokens','—')} | {c.get('requested_output_tokens','—')} | {c.get('completion_tokens','—')} | {c.get('latency_sec','—')} | {c.get('tokens_per_sec','—')} | {c.get('status','ok')} |")
        lines.append("")
    with open(args.md_out, "w", encoding="utf-8") as f: f.write("\n".join(lines)+"\n")
    print(f"Summarized {len(rows)} runs into {args.json_out} and {args.md_out}")

if __name__ == "__main__": main()
