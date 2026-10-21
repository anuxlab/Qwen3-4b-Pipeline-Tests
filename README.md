# Qwen3-4b-Pipeline-Tests
A complete pipeline design to benchmark the performance of different Qwen3-4B variants on GitHub Actions runners. The setup uses a matrix strategy to test multiple quantization levels (Q4_K_M, Q5_K_M, Q8_0) across the two most practical execution methods: Ollama and llama.cpp (via gh-ai-runner/Python).
