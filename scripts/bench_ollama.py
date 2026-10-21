"""End-to-end Ollama benchmark: model metadata, input/context and output limits, latency, memory."""
import argparse, json, os, time, platform, subprocess
from datetime import datetime, timezone
import psutil, requests

OLLAMA = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def ollama_generate(model, prompt, n_ctx, max_tokens, temperature=0.0, timeout=900):
    started = time.perf_counter()
    response = requests.post(f"{OLLAMA}/api/generate", json={
        "model": model, "prompt": prompt, "stream": False,
        "options": {"num_predict": max_tokens, "temperature": temperature,
                    "top_p": 0.95, "num_ctx": n_ctx, "seed": 42},
    }, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    elapsed = time.perf_counter() - started
    eval_count = int(data.get("eval_count") or 0)
    eval_ns = int(data.get("eval_duration") or 0)
    prompt_count = data.get("prompt_eval_count")
    return {
        "status": "ok", "model": model, "n_ctx": n_ctx,
        "requested_output_tokens": max_tokens, "prompt_tokens": prompt_count,
        "completion_tokens": eval_count,
        "input_context_utilization": round(prompt_count / n_ctx, 4) if prompt_count else None,
        "latency_sec": round(elapsed, 3),
        "ttft_sec": round((int(data.get("load_duration") or 0) + int(data.get("prompt_eval_duration") or 0)) / 1e9, 3),
        "tokens_per_sec": round(eval_count / (eval_ns / 1e9), 2) if eval_ns else None,
        "prompt_eval_sec": round(int(data.get("prompt_eval_duration") or 0) / 1e9, 3),
        "generation_sec": round(eval_ns / 1e9, 3) if eval_ns else None,
        "load_sec": round(int(data.get("load_duration") or 0) / 1e9, 3),
        "done_reason": data.get("done_reason"),
        "output_limit_reached": eval_count >= max_tokens,
        "response_excerpt": (data.get("response") or "")[:240],
    }


def get_model_info(model):
    try:
        r = requests.post(f"{OLLAMA}/api/show", json={"model": model}, timeout=30)
        r.raise_for_status(); d = r.json()
        details = d.get("details") or {}
        return {"family": details.get("family"), "parameter_size": details.get("parameter_size"),
                "quantization": details.get("quantization_level"), "format": details.get("format")}
    except Exception as exc:
        return {"metadata_error": str(exc)}


def make_prompt(target_tokens, sentinel):
    # Approximate tokenizer-independent sizing, then record the exact prompt_eval_count returned by Ollama.
    prefix = ("You are being benchmarked. Read the passage carefully. "
              "The unique answer token is ORCHID. If asked, return only that token.\n\n")
    unit = "The river crosses a green valley, and the passage marker is ORCHID. "
    desired_chars = max(0, target_tokens * 4 - len(prefix) - len(sentinel))
    body = (unit * (desired_chars // len(unit) + 1))[:desired_chars]
    return prefix + body + "\n\nQuestion: What is the unique answer token? Return only the token."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--contexts", default="512,1024,2048,4096,8192")
    ap.add_argument("--input-targets", default="128,512,1024,2048,4096")
    ap.add_argument("--output-limits", default="32,128,512")
    ap.add_argument("--output-json", default="results/result.json")
    ap.add_argument("--max-cases", type=int, default=0, help="Optional cap for smoke tests")
    args = ap.parse_args()
    contexts = [int(x) for x in args.contexts.split(",") if x.strip()]
    inputs = [int(x) for x in args.input_targets.split(",") if x.strip()]
    outputs = [int(x) for x in args.output_limits.split(",") if x.strip()]
    os.makedirs(os.path.dirname(args.output_json) or ".", exist_ok=True)
    proc = psutil.Process(os.getpid())
    info = get_model_info(args.model)
    cases = [(ctx, inp, out) for ctx in contexts for inp in inputs if inp < ctx - 32 for out in outputs]
    if args.max_cases:
        cases = cases[:args.max_cases]
    results = []
    for ctx, inp, out in cases:
        case_id = f"ctx{ctx}_in{inp}_out{out}"
        try:
            prompt = make_prompt(inp, "ORCHID")
            result = ollama_generate(args.model, prompt, ctx, out)
            result.update({"case_id": case_id, "target_input_tokens": inp,
                           "input_size_error_tokens": (result.get("prompt_tokens") - inp) if result.get("prompt_tokens") is not None else None,
                           "answer_correct": "ORCHID" in result.get("response_excerpt", "").upper()})
        except Exception as exc:
            result = {"case_id": case_id, "status": "error", "model": args.model,
                      "n_ctx": ctx, "target_input_tokens": inp, "requested_output_tokens": out,
                      "error": f"{type(exc).__name__}: {exc}"}
        results.append(result)
        print(json.dumps(result), flush=True)
    try:
        memory_uss = round(proc.memory_full_info().uss / 2**30, 3)
    except Exception:
        memory_uss = None
    payload = {"schema_version": 1, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "ollama", "model": args.model, "model_info": info,
        "runtime": {"python": platform.python_version(), "platform": platform.platform(),
                    "ram_total_gb": round(psutil.virtual_memory().total / 2**30, 2),
                    "process_uss_gb_after": memory_uss},
        "test_plan": {"contexts": contexts, "target_input_tokens": inputs, "output_limits": outputs,
                      "cases_requested": len(contexts) * len(inputs) * len(outputs), "cases_run": len(results)},
        "results": results}
    with open(args.output_json, "w", encoding="utf-8") as f: json.dump(payload, f, indent=2)
    print(f"Wrote {args.output_json}; {sum(r.get('status') == 'ok' for r in results)}/{len(results)} cases succeeded")
    if not results or not any(r.get("status") == "ok" for r in results): raise SystemExit(2)

if __name__ == "__main__": main()
