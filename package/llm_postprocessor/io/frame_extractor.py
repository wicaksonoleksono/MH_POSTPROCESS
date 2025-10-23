"""Frame extraction utilities for LLM analysis."""

import json
from datetime import datetime
from pathlib import Path


class FrameExtractor:
    """Extract LLM frames within conversation timing windows."""

    @staticmethod
    def extract_llm_frames_for_turns(
        llm_analysis_file: Path,
        conversation_file: Path
    ) -> dict:
        """Extract LLM frames within user_timing windows for each turn.

        Args:
            llm_analysis_file: Path to llm_analysis.jsonl (sequential frames per second)
            conversation_file: Path to llm_conversation.json (contains user_timing windows)

        Returns:
            Dictionary mapping turn_number to list of LLM frames within that turn's timing
        """
        if not llm_analysis_file.exists() or not conversation_file.exists():
            return {}

        with open(conversation_file, "r") as f:
            conv_data = json.load(f)

        conversations = conv_data.get("conversations", [])

        llm_frames = []
        with open(llm_analysis_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    frame = json.loads(line)
                    if frame.get("type") == "result":
                        llm_frames.append(frame)
                except json.JSONDecodeError:
                    continue

        if not llm_frames:
            return {}

        first_timestamp = datetime.fromisoformat(llm_frames[0]["timestamp"].replace("Z", "+00:00"))

        turn_frames = {}

        for turn in conversations:
            turn_num = turn.get("turn_number")
            user_timing = turn.get("user_timing", {})

            if not user_timing or user_timing.get("start") is None:
                continue

            start_sec = user_timing["start"]
            end_sec = user_timing["end"]

            frames_in_window = []
            for i, frame in enumerate(llm_frames):
                frame_time_offset = i

                if start_sec <= frame_time_offset <= end_sec:
                    frames_in_window.append(frame)

            if frames_in_window:
                turn_frames[turn_num] = frames_in_window

        return turn_frames
