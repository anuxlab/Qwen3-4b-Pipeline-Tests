# scripts/bench_llamacpp.py
import argparse
import time
import json
import psutil
import os
from gh_ai_runner import ai_call

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True, help="Path to GGUF file")
    parser.add_argument("--prompt", required=True, help="Input prompt")
    parser.add_argument("--n-threads", type=int, default=4, help="CPU threads")
    parser.add_argument("--output-json", default="result.json")
    args = parser.parse_args()

    # Ensure model exists
    if not os.path.exists(args.model_path):
        raise FileNotFoundError(f"Model not found: {args.model_path}")

    # Measure start time and memory
    start_time = time.time()
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024 ** 3)  # GB

    # Run inference via gh-ai-runner (or direct llama-cpp-python)
    # Note: gh-ai-runner's ai_call expects a model identifier like "qwen".
    # For a local file, you might use llama-cpp-python directly:
    # from llama_cpp import Llama
    # llm = Llama(model_path=args.model_path, n_threads=args.n_threads)
    # output = llm(args.prompt, max_tokens=128)
    # response = output['choices'][0]['text']

    # Placeholder for demonstration – replace with actual call:
    # For actual local GGUF, use llama-cpp-python:
    from llama_cpp import Llama
    llm = Llama(model_path=args.model_path, n_threads=args.n_threads, verbose=False)
    output = llm(args.prompt, max_tokens=128, echo=False)
    response = output['choices'][0]['text']

    end_time = time.time()
    mem_after = process.memory_info().rss / (1024 ** 3)

    result = {
        "method": "llamacpp",
        "model": os.path.basename(args.model_path),
        "prompt": args.prompt[:50] + "...",
        "response": response[:200] + "...",
        "latency_sec": round(end_time - start_time, 3),
        "memory_used_gb": round(mem_after - mem_before, 2),
        "n_threads": args.n_threads,
        "ram_total_gb": round(psutil.virtual_memory().total / (1024 ** 3), 2)
    }

    print(json.dumps(result, indent=2))
    with open(args.output_json, "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
