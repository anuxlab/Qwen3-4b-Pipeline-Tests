import argparse, json, os, time
import psutil
from llama_cpp import Llama

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-path", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--n-threads", type=int, default=4)
    p.add_argument("--max-tokens", type=int, default=128)
    p.add_argument("--output-json", default="result.json")
    a = p.parse_args()

    model_path = os.path.realpath(a.model_path)
    if not os.path.exists(model_path):
        raise FileNotFoundError(model_path)

    proc = psutil.Process(os.getpid())
    mem_before = proc.memory_info().rss / 2**30          # GiB

    t0 = time.time()
    llm = Llama(model_path=model_path, n_threads=a.n_threads, verbose=False)
    out = llm(a.prompt, max_tokens=a.max_tokens, echo=False)
    latency = time.time() - t0

    mem_after = proc.memory_info().rss / 2**30           # GiB

    result = {
        "method": "llamacpp",
        "model": os.path.basename(model_path),
        "quant": os.path.basename(model_path).split("-")[-1].replace(".gguf", ""),
        "latency_sec": round(latency, 3),
        "memory_used_gb": round(mem_after - mem_before, 2),
        "ram_total_gb": round(psutil.virtual_memory().total / 2**30, 2),
        "n_threads": a.n_threads,
        "response_excerpt": out["choices"][0]["text"][:200],
    }
    print(json.dumps(result, indent=2))
    with open(a.output_json, "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()