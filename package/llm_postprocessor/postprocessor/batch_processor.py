"""Batch processing for multiple session files."""

import json
import shutil
from pathlib import Path
from typing import Optional

from ..config import Settings, get_settings
from ..io.assessment_loader import AssessmentLoader
from ..io.conversation_loader import ChatHistoryFormatter, ConversationLoader
from ..io.frame_extractor import FrameExtractor
from ..io.json_reader import JsonReader
from ..schemas.input_schemas import SessionData
from ..schemas.output_schemas import AssessmentSummary
from .facial_analyzer import FacialAnalyzer
from .processor import PostProcessor


class BatchFileProcessor:
    """Process multiple session files from data folder."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize batch processor.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self.processor = PostProcessor(self.settings)

    def process_data_folder(
        self,
        data_folder: str | Path = "data",
        output_folder: str | Path = "post_processed",
        session_number: int = 1,
    ) -> dict:
        """Process all session files from data folder.

        Args:
            data_folder: Path to data folder containing user session folders
            output_folder: Path to save processed results
            session_number: Which session to process (default: 1)

        Returns:
            Dictionary with stats: {"processed": count, "failed": count, "results": [...]}
        """
        data_path = Path(data_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        session_pattern = f"*_session{session_number}"
        session_folders = sorted(data_path.glob(session_pattern))

        results = []
        processed_count = 0
        failed_count = 0

        for folder in session_folders:
            conv_file = folder / "llm_conversation.json"

            if not conv_file.exists():
                print(f"⊘ Skipped {folder.name} - no llm_conversation.json")
                continue

            try:
                formatted_conv = ChatHistoryFormatter.format_from_file(conv_file)
                messages = JsonReader.read_conversation(conv_file)
                raw_turns = ConversationLoader.load_turns_without_created_at(conv_file)

                folder_name = folder.name
                parts = folder_name.rsplit("_", 1)
                session_id = parts[-1] if len(parts) > 1 else "session1"
                user_id = parts[0] if len(parts) > 1 else folder_name

                session_data = SessionData(**{
                    "user": {"user_id": user_id, "session_id": session_id},
                    "llm_conversation": messages,
                    "metadata": {
                        "folder_name": folder.name,
                        "data_path": str(conv_file),
                        "formatted_conversation": formatted_conv,
                        "raw_conversation": raw_turns,
                    },
                })

                result = self.processor.process_session(session_data)

                output_subfolder = output_path / folder.name
                output_subfolder.mkdir(parents=True, exist_ok=True)

                phq_src = folder / "phq_analysis.jsonl"
                llm_src = folder / "llm_analysis.jsonl"
                phq_responses_src = folder / "phq_responses.json"
                metadata_src = folder / "metadata.json"

                metadata = dict(result.metadata or {})
                phq_summary = result.phq_summary
                llm_summary = result.llm_summary

                if llm_src.exists():
                    turn_frames = FrameExtractor.extract_llm_frames_for_turns(
                        llm_analysis_file=llm_src,
                        conversation_file=conv_file
                    )
                    if turn_frames:
                        frames_file = output_subfolder / "llm_frames_by_turn.json"
                        with open(frames_file, "w", encoding="utf-8") as f:
                            json.dump(turn_frames, f, indent=2, ensure_ascii=False)
                        metadata["llm_frames_by_turn_file"] = str(frames_file.relative_to(output_path))

                if phq_responses_src.exists():
                    phq_responses_dest = output_subfolder / phq_responses_src.name
                    shutil.copyfile(phq_responses_src, phq_responses_dest)
                    rel_path = str(phq_responses_dest.relative_to(output_path))
                    metadata["phq_responses_file"] = rel_path

                if metadata_src.exists():
                    metadata_dest = output_subfolder / metadata_src.name
                    shutil.copyfile(metadata_src, metadata_dest)
                    rel_path = str(metadata_dest.relative_to(output_path))
                    metadata["session_metadata_file"] = rel_path

                metadata, phq_summary, llm_summary = self._write_facial_analysis_outputs(
                    session_folder=folder,
                    output_root=output_path,
                    output_subfolder=output_subfolder,
                    metadata=metadata,
                    phq_summary=phq_summary,
                    llm_summary=llm_summary,
                )

                result_to_store = result.model_copy(
                    update={
                        "metadata": metadata,
                        "phq_summary": phq_summary,
                        "llm_summary": llm_summary,
                    }
                )

                output_file = output_subfolder / "analysis_result.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result_to_store.model_dump_json(indent=2))

                results.append({
                    "folder": folder.name,
                    "status": "success",
                    "output_path": str(output_file),
                })
                processed_count += 1
                print(f"✓ Processed {folder.name}")

            except Exception as e:
                results.append({
                    "folder": folder.name,
                    "status": "failed",
                    "error": str(e),
                })
                failed_count += 1
                print(f"✗ Failed {folder.name}: {str(e)}")

        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(session_folders),
            "results": results,
        }

    @staticmethod
    def _write_json_file(path: Path, payload: dict) -> None:
        """Write JSON payload to disk."""
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

    @staticmethod
    def _write_jsonl_file(path: Path, records: list[dict]) -> None:
        """Write records to JSONL format."""
        with path.open("w", encoding="utf-8") as fh:
            for record in records:
                fh.write(json.dumps(record, ensure_ascii=False))
                fh.write("\n")

    def _write_facial_analysis_outputs(
        self,
        session_folder: Path,
        output_root: Path,
        output_subfolder: Path,
        metadata: dict,
        phq_summary: Optional[AssessmentSummary],
        llm_summary: Optional[AssessmentSummary],
    ) -> tuple[dict, Optional[AssessmentSummary], Optional[AssessmentSummary]]:
        """Generate facial analysis summaries and write artifacts to disk."""
        facial_dir = output_subfolder / "facial_analysis"
        facial_dir.mkdir(parents=True, exist_ok=True)

        metadata = dict(metadata or {})
        facial_meta = dict(metadata.get("facial_analysis") or {})

        phq_summary_dict, phq_frames = FacialAnalyzer.collect_phq_frames(
            session_folder / "phq_analysis.jsonl"
        )
        if phq_summary_dict:
            phq_summary_path = facial_dir / "phq_summary.json"
            phq_frames_path = facial_dir / "phq_frames.jsonl"
            self._write_json_file(phq_summary_path, phq_summary_dict)
            self._write_jsonl_file(phq_frames_path, phq_frames)

            phq_summary = FacialAnalyzer.merge_summary_extra(phq_summary, phq_summary_dict)

            facial_meta["phq"] = {
                "summary_file": str(phq_summary_path.relative_to(output_root)),
                "frames_file": str(phq_frames_path.relative_to(output_root)),
            }

        llm_summary_dict, llm_frames = FacialAnalyzer.collect_llm_frames(
            session_folder / "llm_analysis.jsonl",
            metadata.get("raw_conversation") or [],
            (metadata.get("session_metadata") or {}).get("llm_analysis"),
        )
        if llm_summary_dict:
            llm_summary_path = facial_dir / "llm_summary.json"
            llm_frames_path = facial_dir / "llm_frames.jsonl"
            self._write_json_file(llm_summary_path, llm_summary_dict)
            self._write_jsonl_file(llm_frames_path, llm_frames)

            llm_summary = FacialAnalyzer.merge_summary_extra(llm_summary, llm_summary_dict)

            facial_meta["llm"] = {
                "summary_file": str(llm_summary_path.relative_to(output_root)),
                "frames_file": str(llm_frames_path.relative_to(output_root)),
                "user_timing_windows": [
                    {
                        "turn_number": turn.get("turn_number"),
                        "start": (turn.get("user_timing") or {}).get("start"),
                        "end": (turn.get("user_timing") or {}).get("end"),
                    }
                    for turn in (metadata.get("raw_conversation") or [])
                    if isinstance(turn, dict) and turn.get("user_timing")
                ],
            }

        if facial_meta:
            metadata["facial_analysis"] = facial_meta

        return metadata, phq_summary, llm_summary
