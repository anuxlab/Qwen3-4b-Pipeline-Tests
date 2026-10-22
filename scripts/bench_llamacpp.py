import argparse, json, os, time
import psutil
from llama_cpp import Llama
try:
    from scripts.prompts import get_suite
except ImportError:
    from prompts import get_suite

def run_one(llm, p, n_ctx):
    t0 = time.time()
    first = None
    text = ""
    for chunk in llm(
        p["prompt"],
        max_tokens=p["max_tokens"],
        temperature=p.get("temperature", 0.7),
        top_p=p.get("top_p", 0.95),
        top_k=p.get("top_k", 40),
        repeat_penalty=p.get("repeat_penalty", 1.1),
        echo=False,
        stream=True,
    ):
        if first is None:
            first = time.time()
        text += chunk["choices"][0]["text"]
    end = time.time()

    prompt_tokens = len(llm.tokenize(p["prompt"].encode("utf-8")))
    completion_tokens = len(llm.tokenize(text.encode("utf-8")))
    gen_time = end - first if first else None

    return {
        "name": p["name"],
        "description": p.get("description"),
        "n_ctx": n_ctx,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "latency_sec": round(end - t0, 3),
        "ttft_sec": round(first - t0, 3) if first else None,
        "tokens_per_sec": round(completion_tokens / gen_time, 2) if gen_time else None,
        "status": "ok",
        "kind": "llamacpp_prompt_suite",
        "response_text": text,
        "response_excerpt": text[:300],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-path", required=True)
    ap.add_argument("--suite", default="quick", choices=["quick", "full", "context"])
    ap.add_argument("--n-ctx", type=int, default=2048)
    ap.add_argument("--n-threads", type=int, default=4)
    ap.add_argument("--output-json", default="result.json")
    args = ap.parse_args()

    model_path = os.path.realpath(args.model_path)
    if not os.path.exists(model_path):
        raise FileNotFoundError(model_path)

    proc = psutil.Process(os.getpid())
    llm = Llama(
        model_path=model_path,
        n_ctx=args.n_ctx,
        n_threads=args.n_threads,
        verbose=False,
    )

    results = []
    for p in get_suite(args.suite):
        results.append(run_one(llm, p, args.n_ctx))

    # USS AFTER inference — the truest resident footprint
    mem_uss = proc.memory_full_info().uss / 2**30

    payload = {
        "schema_version": 2,
        "method": "llamacpp",
        "model_info": {"quantization": os.path.basename(model_path).split("-")[-1].replace(".gguf", "")},
        "runtime": {"python": __import__("platform").python_version(), "platform": __import__("platform").platform()},
        "model": os.path.basename(model_path),
        "quant": os.path.basename(model_path).split("-")[-1].replace(".gguf", ""),
        "n_threads": args.n_threads,
        "n_ctx": args.n_ctx,
        "memory_uss_gb": round(mem_uss, 2),
        "ram_total_gb": round(psutil.virtual_memory().total / 2**30, 2),
        "results": results,
    }

    print(json.dumps(payload, indent=2))
    with open(args.output_json, "w") as f:
        json.dump(payload, f, indent=2)

if __name__ == "__main__":
    main()