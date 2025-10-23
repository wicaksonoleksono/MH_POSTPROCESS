"""Assessment file loading utilities."""

import json
from pathlib import Path
from typing import Optional

from ..schemas.output_schemas import AssessmentSummary


class AssessmentLoader:
    """Load and parse assessment files."""

    @staticmethod
    def load_assessment_summary(file_path: Optional[Path]) -> Optional[AssessmentSummary]:
        """Read a JSONL assessment file and return a lightweight summary."""
        if not file_path or not file_path.exists():
            return None

        metadata_entry = None
        total_rows = 0
        with open(file_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total_rows += 1
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if metadata_entry is None and payload.get("type") == "metadata":
                    metadata_entry = payload

        data_rows = total_rows - (1 if metadata_entry else 0)
        if data_rows < 0:
            data_rows = 0

        return AssessmentSummary(
            metadata=metadata_entry,
            total_rows=total_rows,
            data_rows=data_rows,
        )

    @staticmethod
    def load_json(file_path: Optional[Path]) -> Optional[dict]:
        """Safely load a JSON file if it exists."""
        if not file_path or not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return None
