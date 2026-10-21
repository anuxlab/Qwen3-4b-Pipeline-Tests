import argparse, json, os, time
import psutil, requests
from prompts import get_suite

def run_one(model, p, n_ctx):
    t0 = time.time()
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": p["prompt"],
            "stream": False,
            "options": {
                "num_predict": p["max_tokens"],
                "temperature": p.get("temperature", 0.7),
                "top_p": p.get("top_p", 0.95),
                "top_k": p.get("top_k", 40),
                "repeat_penalty": p.get("repeat_penalty", 1.1),
                "num_ctx": n_ctx,
            },
        },
        timeout=600,
    )
    end = time.time()
    data = resp.json()

    eval_count = data.get("eval_count", 0)
    eval_ns = data.get("eval_duration", 0)
    tps = round(eval_count / (eval_ns / 1e9), 2) if eval_ns else None

    return {
        "name": p["name"],
        "description": p.get("description"),
        "n_ctx": n_ctx,
        "prompt_tokens": data.get("prompt_eval_count"),
        "completion_tokens": eval_count,
        "latency_sec": round(end - t0, 3),
        "ttft_sec": round((data.get("load_duration", 0) + data.get("prompt_eval_duration", 0)) / 1e9, 3),
        "tokens_per_sec": tps,
        "response_excerpt": data.get("response", "")[:300],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--suite", default="quick", choices=["quick", "full"])
    ap.add_argument("--n-ctx", type=int, default=2048)
    ap.add_argument("--output-json", default="result.json")
    args = ap.parse_args()

    proc = psutil.Process(os.getpid())
    results = [run_one(args.model, p, args.n_ctx) for p in get_suite(args.suite)]

    payload = {
        "method": "ollama",
        "model": args.model,
        "n_ctx": args.n_ctx,
        "memory_uss_gb": round(proc.memory_full_info().uss / 2**30, 2),
        "ram_total_gb": round(psutil.virtual_memory().total / 2**30, 2),
        "results": results,
    }
    print(json.dumps(payload, indent=2))
    with open(args.output_json, "w") as f:
        json.dump(payload, f, indent=2)

if __name__ == "__main__":
    main()