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
            # AI message first
            ai_msg = turn.get("ai_message")
            if ai_msg:
                messages.append({"role": "ai", "content": ai_msg})

            # Then user message
            user_msg = turn.get("user_message")
            if user_msg:
                messages.append({"role": "user", "content": user_msg})

        return messages

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
            # AI message first
            ai_msg = turn.get("ai_message")
            if ai_msg:
                messages.append({"role": "ai", "content": ai_msg})

            # Then user message
            user_msg = turn.get("user_message")
            if user_msg:
                messages.append({"role": "user", "content": user_msg})

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
            # AI message first
            ai_msg = turn.get("ai_message")
            if ai_msg:
                messages.append({"role": "ai", "content": ai_msg})

            # Then user message
            user_msg = turn.get("user_message")
            if user_msg:
                messages.append({"role": "user", "content": user_msg})

        return messages
