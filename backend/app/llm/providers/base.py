from abc import ABC, abstractmethod
from typing import Tuple
from app.llm.models import LLMHealthStatus, TokenMetrics, LLMConfig

class BaseLLMProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    def health_check(self) -> LLMHealthStatus:
        pass

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> Tuple[str, TokenMetrics]:
        pass
