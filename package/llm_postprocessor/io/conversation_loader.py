"""Load and transform conversation data."""

import json
from pathlib import Path
from typing import Optional


class ConversationLoader:
    """Load conversations from JSON and transform to clean format."""

    @staticmethod
    def load_from_file(file_path: str | Path) -> list[dict[str, str]]:
        """Load conversation from JSON file and convert to clean format.

        Args:
            file_path: Path to llm_conversation.json

        Returns:
            List of alternating [user, ai, user, ai, ...] messages
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        conversations = data.get("conversations", [])
        messages = []

        for turn in conversations:
            # User message first
            user_msg = turn.get("user_message")
            if user_msg:
                messages.append({"role": "user", "content": user_msg})

            # Then AI message
            ai_msg = turn.get("ai_message")
            if ai_msg:
                messages.append({"role": "ai", "content": ai_msg})

        return messages

    @staticmethod
    def load_turns_without_created_at(file_path: str | Path) -> list[dict]:
        """Load raw conversation turns without created_at timestamp."""
        with open(file_path, "r") as f:
            data = json.load(f)

        conversations = data.get("conversations", [])
        cleaned_turns: list[dict] = []

        for turn in conversations:
            cleaned = {}
            if "turn_number" in turn:
                cleaned["turn_number"] = turn["turn_number"]

            user_msg = turn.get("user_message")
            if user_msg is not None:
                cleaned["user_message"] = user_msg

            ai_msg = turn.get("ai_message")
            if ai_msg is not None:
                cleaned["ai_message"] = ai_msg

            if "user_message_length" in turn:
                cleaned["user_message_length"] = turn["user_message_length"]
            if "user_timing" in turn:
                cleaned["user_timing"] = turn["user_timing"]
            if "ai_timing" in turn:
                cleaned["ai_timing"] = turn["ai_timing"]
            if "has_end_conversation" in turn:
                cleaned["has_end_conversation"] = turn["has_end_conversation"]
            if "ai_model_used" in turn:
                cleaned["ai_model_used"] = turn["ai_model_used"]

            cleaned_turns.append(cleaned)

        return cleaned_turns

    @staticmethod
    def load_raw(data: dict) -> list[dict[str, str]]:
        """Convert raw conversation dict to clean format.

        Args:
            data: Raw conversation data from JSON

        Returns:
            Clean message list
        """
        conversations = data.get("conversations", [])
        messages = []

        for turn in conversations:
            # User message first
            user_msg = turn.get("user_message")
            if user_msg:
                messages.append({"role": "user", "content": user_msg})

            # Then AI message
            ai_msg = turn.get("ai_message")
            if ai_msg:
                messages.append({"role": "ai", "content": ai_msg})

        return messages

    @staticmethod
    def transform_conversation(conversations: list[dict]) -> list[dict[str, str]]:
        """Transform conversation list to alternating format.

        Args:
            conversations: List of conversation turns

        Returns:
            Clean alternating [user, ai, user, ai] format
        """
        messages = []

        for turn in conversations:
            # User message first
            user_msg = turn.get("user_message")
            if user_msg:
                messages.append({"role": "user", "content": user_msg})

            # Then AI message
            ai_msg = turn.get("ai_message")
            if ai_msg:
                messages.append({"role": "ai", "content": ai_msg})

        return messages


class ChatHistoryFormatter:
    """Format conversation messages for LLM prompts."""

    # Role mapping configurations
    ROLE_MAP = {
        "user": "mahasiswa",
        "ai": "sindi",
    }

    @staticmethod
    def validate_messages(messages: list[dict[str, str]]) -> bool:
        """Validate message structure.

        Args:
            messages: List of message dicts

        Returns:
            True if valid, False otherwise
        """
        if not messages:
            return False

        for msg in messages:
            if not isinstance(msg, dict):
                return False
            if "role" not in msg or "content" not in msg:
                return False
            if not msg.get("content"):
                return False

        return True

    @staticmethod
    def format_messages(
        messages: list[dict[str, str]],
        role_map: dict[str, str] | None = None,
        include_metadata: bool = False,
    ) -> str:
        """Format messages to structured format.

        Args:
            messages: List of {"role": "user"|"ai", "content": "..."} dicts
            role_map: Custom role mapping (default: {"user": "mahasiswa", "ai": "sindi"})
            include_metadata: Include turn numbers and stats (default: False)

        Returns:
            Formatted conversation string
        """
        if not ChatHistoryFormatter.validate_messages(messages):
            raise ValueError("Invalid message structure")

        role_map = role_map or ChatHistoryFormatter.ROLE_MAP
        formatted_lines = []

        greeting_role = role_map.get("ai", "ai")
        greeting_content = "Halo aku Sindi, apakabar"
        if include_metadata:
            formatted_lines.append(f"[Turn 0] {greeting_role}: {greeting_content}")
        else:
            formatted_lines.append(f"{greeting_role}: {greeting_content}")

        for turn, msg in enumerate(messages, 1):
            role = msg.get("role", "")
            content = msg.get("content", "").strip()

            if role and content:
                formatted_role = role_map.get(role, role)

                if include_metadata:
                    formatted_lines.append(f"[Turn {turn}] {formatted_role}: {content}")
                else:
                    formatted_lines.append(f"{formatted_role}: {content}")

        return "\n".join(formatted_lines)

    @staticmethod
    def format_from_file(
        file_path: str | Path,
        role_map: dict[str, str] | None = None,
        include_metadata: bool = False,
    ) -> str:
        """Load conversation from file and format for prompts.

        Args:
            file_path: Path to llm_conversation.json
            role_map: Custom role mapping
            include_metadata: Include turn numbers and stats

        Returns:
            Formatted conversation string
        """
        messages = ConversationLoader.load_from_file(file_path)
        return ChatHistoryFormatter.format_messages(
            messages, role_map=role_map, include_metadata=include_metadata
        )

    @staticmethod
    def get_stats(messages: list[dict[str, str]]) -> dict:
        """Get conversation statistics.

        Args:
            messages: List of messages

        Returns:
            Dictionary with stats: {"total": count, "mahasiswa": count, "sindi": count, "avg_length": float}
        """
        if not messages:
            return {"total": 0, "mahasiswa": 0, "sindi": 0, "avg_length": 0.0}

        role_counts = {"user": 0, "ai": 0}
        total_chars = 0

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role in role_counts:
                role_counts[role] += 1
            total_chars += len(content)

        total = len(messages)
        avg_length = total_chars / total if total > 0 else 0

        return {
            "total": total,
            "mahasiswa": role_counts["user"],
            "sindi": role_counts["ai"],
            "avg_length": round(avg_length, 2),
            "total_chars": total_chars,
        }
