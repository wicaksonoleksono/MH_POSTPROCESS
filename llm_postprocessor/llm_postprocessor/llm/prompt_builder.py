"""Prompt builder for constructing LLM conversation chains."""

from typing import Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from llm_postprocessor.schemas.aspects import PHQAspects
from llm_postprocessor.schemas.scale import PHQScales
from llm_postprocessor.llm.prompts import (
    HUMAN_INST_1,
    AI_RESPONSE_1,
    HUMAN_INST_2,
    AI_RESPONSE_2,
    HUMAN_INST_3,
)


class PromptBuilder:
    """Builder for constructing multi-turn conversation prompts."""

    def __init__(self):
        """Initialize prompt builder."""
        self.aspects = PHQAspects()
        self.scales = PHQScales()

    def build_analysis_messages(
        self, chat_history: list[dict[str, str]]
    ) -> list[HumanMessage | AIMessage]:
        """Build complete message chain for analysis.

        Args:
            chat_history: List of conversation messages

        Returns:
            List of LangChain messages (HumanMessage, AIMessage)
        """
        messages = []
        human_msg_1 = HumanMessage(
            content=HUMAN_INST_1.format()
        )
        messages.append(human_msg_1)
        ai_msg_1 = AIMessage(
            content=AI_RESPONSE_1.format()
        )
        messages.append(ai_msg_1)
        aspects_str = PHQAspects.get_aspect()
        phq_scale_str = PHQScales.format_scale("phq_scale")
        operational_scale_str = PHQScales.format_scale("operational_scale")
        human_msg_2 = HumanMessage(
            content=HUMAN_INST_2.format(
                aspects=aspects_str,
                phq_scale=phq_scale_str,
                operational_scale=operational_scale_str,
            )
        )
        messages.append(human_msg_2)
        ai_msg_2 = AIMessage(
            content=AI_RESPONSE_2.format()
        )
        messages.append(ai_msg_2)
        chat_history_str = self._format_chat_history(chat_history)
        human_msg_3 = HumanMessage(
            content=HUMAN_INST_3.format(chatHistory=chat_history_str)
        )
        messages.append(human_msg_3)

        return messages

    def _format_chat_history(self, chat_history: list[dict[str, str]]) -> str:
        """Format chat history into readable string.

        Args:
            chat_history: List of chat messages

        Returns:
            Formatted string representation
        """
        formatted = []
        for i, msg in enumerate(chat_history, 1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"Turn {i} [{role}]: {content}")

        return "\n".join(formatted)

    def build_system_message(self, custom_instruction: str = None) -> SystemMessage:
        """Build optional system message.

        Args:
            custom_instruction: Optional custom system instruction

        Returns:
            SystemMessage
        """
        if custom_instruction:
            return SystemMessage(content=custom_instruction)

        return SystemMessage(
            content="Anda adalah asisten analisis psikologi yang objektif dan teliti."
        )
