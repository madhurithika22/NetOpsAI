# NetOps LLM Audit

Detailed audit of `LLMGateway`, `OllamaProvider`, and `MockLLMProvider`.
Benchmark scripts attempt real Ollama inference at `http://localhost:11434`, but silently fall back to `MockLLMProvider` if Ollama is unreachable.
