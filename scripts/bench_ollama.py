# scripts/bench_ollama.py
import time
import psutil
import json
import sys

def main():
    # In a real scenario, you would trigger the action externally.
    # For simplicity, we assume the response is passed as an argument.
    # In the YAML, we capture the response length; here we mock timing.
    print("Ollama benchmark placeholder – timing is captured via shell 'time'.")
    # A more robust approach would use `time` in the shell step.
    # Example: time ollama run model "prompt"
    result = {
        "method": "ollama",
        "status": "completed",
        "note": "Use 'time' shell command for precise latency"
    }
    with open("result.json", "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
