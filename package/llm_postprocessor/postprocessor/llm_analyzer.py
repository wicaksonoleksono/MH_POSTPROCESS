"""LLM Analyzer for processing conversations."""

import json
from typing import Optional

from ..llm.client import LLMClient
from ..llm.prompt_builder import PromptBuilder
from ..schemas.llm_analysis_schemas import (
    LLMAnalysisInput,
    LLMAnalysisOutput,
)


class LLMAnalyzer:
    """Analyzer for LLM conversation using prompt builder."""

    def __init__(self, llm_client: LLMClient):
        """Initialize analyzer.

        Args:
            llm_client: LLM client to use for analysis
        """
        self.llm_client = llm_client
        self.prompt_builder = PromptBuilder()

    def analyze(
        self, analysis_input: LLMAnalysisInput | dict
    ) -> LLMAnalysisOutput:
        """Analyze conversation and return structured output.

        Args:
            analysis_input: Input data (LLMAnalysisInput or dict)

        Returns:
            LLMAnalysisOutput with structured analysis results
        """
        # Validate and convert input
        if isinstance(analysis_input, dict):
            analysis_input = LLMAnalysisInput(**analysis_input)

        # Build messages using prompt builder
        messages = self.prompt_builder.build_analysis_messages(
            analysis_input.chat_history
        )

        # Get LLM and invoke
        llm = self.llm_client.get_client()
        response = llm.invoke(messages)

        # Parse and validate response
        try:
            result_dict = json.loads(response.content)
            return LLMAnalysisOutput(**result_dict)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")
        except Exception as e:
            raise ValueError(f"Failed to validate LLM output: {e}")

    def analyze_batch(
        self, inputs: list[LLMAnalysisInput | dict]
    ) -> list[LLMAnalysisOutput]:
        """Analyze multiple conversations.

        Args:
            inputs: List of analysis inputs

        Returns:
            List of analysis outputs
        """
        return [self.analyze(input_data) for input_data in inputs]
