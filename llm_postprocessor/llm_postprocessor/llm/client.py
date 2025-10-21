"""LLM client wrapper for different providers."""

from abc import ABC, abstractmethod
from typing import Any
from langchain_openai import ChatOpenAI
from langchain_core.language_model import BaseLanguageModel
class LLMClient(ABC):
    """Abstract LLM client."""
    @abstractmethod
    def get_client(self) -> BaseLanguageModel:
        """Get LangChain LLM client."""
        pass

class OpenAIClient(LLMClient):
    """OpenAI LLM client."""

    def __init__(
        self,
        model_name: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_client(self) -> BaseLanguageModel:
        """Get OpenAI LLM client (reads OPENAI_API_KEY from env)."""
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )


class TogetherAIClient(LLMClient):
    """TogetherAI LLM client."""

    def __init__(
        self,
        model_name: str = "mistralai/Mistral-7B-Instruct-v0.1",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_client(self) -> BaseLanguageModel:
        """Get TogetherAI LLM client (reads TOGETHER_API_KEY from env)."""
        from langchain_community.llms import Together

        return Together(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
