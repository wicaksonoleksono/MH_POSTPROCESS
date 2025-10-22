"""JSON file writer."""

import json
from pathlib import Path
from typing import Any

from llm_postprocessor.schemas.output_schemas import ProcessedResult


class JsonWriter:
    """Write JSON files."""

    @staticmethod
    def write_json(
        data: dict[str, Any] | Any, file_path: str | Path, indent: int = 2
    ) -> None:
        """Write data to JSON file.

        Args:
            data: Data to write
            file_path: Path to output JSON file
            indent: JSON indentation level
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        if hasattr(data, "model_dump"):
            # Pydantic model
            data = data.model_dump()

        with open(file_path, "w") as f:
            json.dump(data, f, indent=indent, default=str)

    @staticmethod
    def write_jsonl(
        data: list[ProcessedResult | dict[str, Any]], file_path: str | Path
    ) -> None:
        """Write data to JSONL (JSON Lines) file.

        Args:
            data: List of data to write
            file_path: Path to output JSONL file
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            for item in data:
                if hasattr(item, "model_dump"):
                    # Pydantic model
                    item = item.model_dump()
                f.write(json.dumps(item, default=str) + "\n")

    @staticmethod
    def write_result(result: ProcessedResult, file_path: str | Path) -> None:
        """Write ProcessedResult to JSON file.

        Args:
            result: ProcessedResult object
            file_path: Path to output JSON file
        """
        JsonWriter.write_json(result, file_path)
