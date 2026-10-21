# scripts/prompts.py

QUICK_PROMPTS = [
    {
        "name": "short_factual",
        "prompt": "What is the capital of France? Answer in one word.",
        "max_tokens": 10,
        "description": "Minimal output; overhead baseline",
    },
    {
        "name": "reasoning_bat_ball",
        "prompt": (
            "A bat and a ball cost $1.10 total. The bat costs $1.00 more than the ball. "
            "How much does the ball cost? Answer with just the number, then explain in one sentence."
        ),
        "max_tokens": 80,
        "description": "Reasoning quality; correct answer is $0.05",
    },
    {
        "name": "format_constraint",
        "prompt": (
            "List exactly three primary colors. Use the format: "
            "1. <color> 2. <color> 3. <color>. Do not add any other text."
        ),
        "max_tokens": 40,
        "description": "Strict instruction-following / quantization damage",
    },
]

FULL_PROMPTS = QUICK_PROMPTS + [
    {
        "name": "medium_explain",
        "prompt": "Explain the significance of the Turing Test in 50 words.",
        "max_tokens": 100,
        "description": "Fluency and coherence",
    },
    {
        "name": "long_output",
        "prompt": (
            "Write a detailed 300-word explanation of how neural networks learn, "
            "including forward propagation, loss functions, and backpropagation."
        ),
        "max_tokens": 400,
        "description": "Sustained generation throughput",
    },
    {
        "name": "long_context_qa",
        "prompt": (
            "Read the following passage and answer the question at the end.\n\n"
            + ("The quick brown fox jumps over the lazy dog. " * 200)
            + "\n\nQuestion: What animal jumps over the lazy dog? Answer in one word."
        ),
        "max_tokens": 10,
        "description": "Long-input processing (~2600 tokens)",
    },
]

CONTEXT_PROMPTS = [
    {
        "name": "context_fill",
        "prompt": (
            "Summarize the following text in one sentence.\n\n"
            + ("The quick brown fox jumps over the lazy dog. " * 400)
            + "\n\nOne-sentence summary:"
        ),
        "max_tokens": 50,
        "description": "Fills the context window; tests prefill cost",
    }
]

def get_suite(name: str):
    return {"quick": QUICK_PROMPTS, "full": FULL_PROMPTS, "context": CONTEXT_PROMPTS}[name]