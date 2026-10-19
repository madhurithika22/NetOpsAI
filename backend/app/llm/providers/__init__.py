from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.ollama import OllamaProvider
from app.llm.providers.openai import OpenAICompatibleProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.models import LLMConfig

def get_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    provider_type = (config.provider or "ollama").lower()
    if provider_type == "ollama":
        return OllamaProvider(config)
    elif provider_type in ["openai", "vllm", "lmstudio"]:
        return OpenAICompatibleProvider(config)
    elif provider_type == "mock":
        return MockLLMProvider(config)
    else:
        return OllamaProvider(config)
