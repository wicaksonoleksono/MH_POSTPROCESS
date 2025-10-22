"""Configuration management for LLM Post-processor."""

from typing import Literal

from pydantic import Field

try:
    # Prefer dedicated package available in Pydantic v2 ecosystem
    from pydantic_settings import BaseSettings  # type: ignore
except ImportError:  # pragma: no cover
    try:
        # Fallback for Pydantic v1 where BaseSettings lives in pydantic itself
        from pydantic import BaseSettings  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "pydantic-settings is required when using pydantic>=2.0. "
            "Install with `pip install llm-postprocessor[settings]`."
        ) from exc


class LLMSettings(BaseSettings):
    """Settings for LLM configuration."""

    provider: Literal["openai", "togetherai"] = Field(
        default="openai", description="LLM provider to use"
    )
    model_name: str = Field(
        default="gpt-3.5-turbo", description="Model name to use"
    )
    temperature: float = Field(default=0.7, description="Model temperature")
    max_tokens: int = Field(default=2000, description="Maximum tokens in response")

    class Config:
        env_file = ".env"
        env_prefix = "LLM_"


class ProcessorSettings(BaseSettings):
    """Settings for the post-processor."""

    input_dir: str = Field(default="./data", description="Input data directory")
    output_dir: str = Field(default="./output", description="Output directory")
    batch_size: int = Field(default=10, description="Batch size for processing")

    class Config:
        env_file = ".env"
        env_prefix = "PROCESSOR_"


class Settings(BaseSettings):
    """Main settings class."""

    llm: LLMSettings = Field(default_factory=LLMSettings)
    processor: ProcessorSettings = Field(default_factory=ProcessorSettings)

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
