"""Lightweight configuration helpers without external dependencies."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable


def _get_env(
    key: str,
    default,
    cast: Callable[[str], object] | None = None,
):
    """Read environment variable and cast when possible."""
    value = os.getenv(key)
    if value is None:
        return default
    if cast is None:
        return value
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: str) -> float:
    return float(value.strip())


def _to_int(value: str) -> int:
    return int(value.strip())


@dataclass
class LLMSettings:
    """Configuration for LLM provider."""

    provider: str = "openai"
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 2000

    @classmethod
    def from_env(cls) -> "LLMSettings":
        return cls(
            provider=_get_env("LLM_PROVIDER", cls.provider, str),
            model_name=_get_env("LLM_MODEL_NAME", cls.model_name, str),
            temperature=_get_env("LLM_TEMPERATURE", cls.temperature, _to_float),
            max_tokens=_get_env("LLM_MAX_TOKENS", cls.max_tokens, _to_int),
        )


@dataclass
class ProcessorSettings:
    """Configuration for the post-processor."""

    input_dir: str = "./data"
    output_dir: str = "./output"
    batch_size: int = 10

    @classmethod
    def from_env(cls) -> "ProcessorSettings":
        return cls(
            input_dir=_get_env("PROCESSOR_INPUT_DIR", cls.input_dir, str),
            output_dir=_get_env("PROCESSOR_OUTPUT_DIR", cls.output_dir, str),
            batch_size=_get_env("PROCESSOR_BATCH_SIZE", cls.batch_size, _to_int),
        )


@dataclass
class Settings:
    """Aggregate settings container."""

    llm: LLMSettings = field(default_factory=LLMSettings)
    processor: ProcessorSettings = field(default_factory=ProcessorSettings)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm=LLMSettings.from_env(),
            processor=ProcessorSettings.from_env(),
        )


def get_settings() -> Settings:
    """Return settings populated from environment variables."""
    return Settings.from_env()
