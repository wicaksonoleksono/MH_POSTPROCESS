"""JSON file reader."""

import json
from pathlib import Path
from typing import Any

from llm_postprocessor.schemas.input_schemas import SessionData


class JsonReader:
    """Read JSON files."""

    @staticmethod
    def read_json(file_path: str | Path) -> dict[str, Any]:
        """Read JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON data
        """
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def read_session_data(file_path: str | Path) -> SessionData:
        """Read session data from JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            SessionData object
        """
        data = JsonReader.read_json(file_path)
        return SessionData(**data)

    @staticmethod
    def read_jsonl(file_path: str | Path) -> list[dict[str, Any]]:
        """Read JSONL (JSON Lines) file.

        Args:
            file_path: Path to JSONL file

        Returns:
            List of parsed JSON objects
        """
        results = []
        with open(file_path, "r") as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))
        return results
