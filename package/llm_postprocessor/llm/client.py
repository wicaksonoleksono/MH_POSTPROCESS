"""LLM client wrapper for different providers."""

from abc import ABC, abstractmethod

from langchain_openai import ChatOpenAI
from langchain_together import ChatTogether
from langchain_core.language_models import BaseChatModel

class LLMClient(ABC):
    """Abstract LLM client."""
    @abstractmethod
    def get_client(self) -> BaseChatModel:
        """Get LangChain LLM client."""
        pass

class OpenAIClient(LLMClient):
    """OpenAI LLM client."""

    def __init__(
        self,
        model_name: str = "",
        temperature: float = 0,
        seed:int=42,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.seed = seed

    def get_client(self) -> BaseChatModel:
        """Get OpenAI LLM client (reads OPENAI_API_KEY from env)."""
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            seed = self.seed
        )

class TogetherAIClient(LLMClient):
    """TogetherAI LLM client."""

    def __init__(
        self,
        model_name: str = "",
        temperature: float = 0,
        seed : int = 42,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.seed = seed

    def get_client(self) -> BaseChatModel:
        """Get TogetherAI LLM client (reads TOGETHER_API_KEY from env)."""
        return ChatTogether(
            model=self.model_name,
            temperature=self.temperature,
            seed=self.seed
        )
