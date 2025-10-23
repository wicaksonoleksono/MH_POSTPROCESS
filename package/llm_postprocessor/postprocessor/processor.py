"""Main post-processor class."""

import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config import Settings, get_settings
from ..schemas.input_schemas import SessionData
from ..schemas.output_schemas import AssessmentSummary, ProcessedResult
from ..io.json_reader import JsonReader
from ..io.conversation_loader import ChatHistoryFormatter, ConversationLoader


class PostProcessor:
    """Main post-processor responsible for conversation formatting."""

    def __init__(self, settings: Optional[Settings] = None):
        """Initialize post-processor.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()

    def process_session(self, session_data: SessionData) -> ProcessedResult:
        """Process a single session.

        Args:
            session_data: Input session data

        Returns:
            ProcessedResult containing formatted conversation and assessment summaries.
        """
        metadata = dict(session_data.metadata or {})
        data_path = metadata.get("data_path")
        session_folder = Path(data_path).parent if data_path else None

        phq_summary = self._load_assessment_summary(
            session_folder / "phq_analysis.jsonl" if session_folder else None
        )
        llm_summary = self._load_assessment_summary(
            session_folder / "llm_analysis.jsonl" if session_folder else None
        )

        phq_responses = self._load_json(session_folder / "phq_responses.json" if session_folder else None)
        session_metadata = self._load_json(session_folder / "metadata.json" if session_folder else None)

        if session_metadata:
            metadata["session_metadata"] = session_metadata

        if phq_summary:
            extra = phq_summary.extra.copy() if phq_summary.extra else {}
            if phq_responses:
                extra.update({
                    "total_score": phq_responses.get("total_score"),
                    "max_possible_score": phq_responses.get("max_possible_score"),
                    "responses": phq_responses.get("responses"),
                })
            if session_metadata and session_metadata.get("phq_analysis"):
                extra["analysis_stats"] = session_metadata["phq_analysis"]
            if extra:
                phq_summary = phq_summary.model_copy(update={"extra": extra})

        if llm_summary and session_metadata and session_metadata.get("llm_analysis"):
            extra = llm_summary.extra.copy() if llm_summary.extra else {}
            extra["analysis_stats"] = session_metadata["llm_analysis"]
            llm_summary = llm_summary.model_copy(update={"extra": extra})

        return ProcessedResult(
            user_id=session_data.user.user_id,
            session_id=session_data.user.session_id,
            metadata=metadata,
            phq_summary=phq_summary,
            llm_summary=llm_summary,
        )

    @staticmethod
    def _load_assessment_summary(file_path: Optional[Path]) -> Optional[AssessmentSummary]:
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
    def _load_json(file_path: Optional[Path]) -> Optional[dict]:
        """Safely load a JSON file if it exists."""
        if not file_path or not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as fh:
            try:
                return json.load(fh)
            except json.JSONDecodeError:
                return None

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

        # Load conversation to get timing windows
        with open(conversation_file, "r") as f:
            conv_data = json.load(f)

        conversations = conv_data.get("conversations", [])

        # Load all LLM frames
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

        # Get first frame timestamp as reference (video start time)
        if not llm_frames:
            return {}

        from datetime import datetime
        first_timestamp = datetime.fromisoformat(llm_frames[0]["timestamp"].replace("Z", "+00:00"))

        # Map frames to turns based on user_timing windows
        turn_frames = {}

        for turn in conversations:
            turn_num = turn.get("turn_number")
            user_timing = turn.get("user_timing", {})

            if not user_timing or user_timing.get("start") is None:
                continue

            start_sec = user_timing["start"]
            end_sec = user_timing["end"]

            # Filter frames within this timing window
            frames_in_window = []
            for i, frame in enumerate(llm_frames):
                # Frame index is sequential (per second)
                # Assuming frames are 1 per second, frame index ≈ seconds from start
                frame_time_offset = i  # seconds from video start

                if start_sec <= frame_time_offset <= end_sec:
                    frames_in_window.append(frame)

            if frames_in_window:
                turn_frames[turn_num] = frames_in_window

        return turn_frames

    def process_batch(self, sessions: list[SessionData]) -> list[ProcessedResult]:
        """Process multiple sessions.

        Args:
            sessions: List of session data

        Returns:
            List of processed results
        """
        results = []
        for session in sessions:
            result = self.process_session(session)
            results.append(result)
        return results


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

        # Find all session folders matching pattern
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
                # Load and format conversation
                formatted_conv = ChatHistoryFormatter.format_from_file(conv_file)

                # Load raw messages for processing
                messages = JsonReader.read_conversation(conv_file)
                raw_turns = ConversationLoader.load_turns_without_created_at(conv_file)

                # Extract user_id and session_id from folder name
                # Format: user_11_miko_session1 -> user_id=user_11, session_id=session1
                folder_name = folder.name
                parts = folder_name.rsplit("_", 1)
                session_id = parts[-1] if len(parts) > 1 else "session1"
                user_id = parts[0] if len(parts) > 1 else folder_name

                # Create session data
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

                # Process session
                result = self.processor.process_session(session_data)

                # Save result and copy supporting analysis files
                output_subfolder = output_path / folder.name
                output_subfolder.mkdir(parents=True, exist_ok=True)

                phq_src = folder / "phq_analysis.jsonl"
                llm_src = folder / "llm_analysis.jsonl"
                phq_responses_src = folder / "phq_responses.json"
                metadata_src = folder / "metadata.json"

                metadata = dict(result.metadata or {})
                phq_summary = result.phq_summary
                llm_summary = result.llm_summary

                # Extract LLM frames by turn and save (no copying jsonl files)
                if llm_src.exists():
                    turn_frames = self.processor.extract_llm_frames_for_turns(
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
                    # Use model_dump_json for proper serialization
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
    def _parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime strings, handling 'Z' suffix."""
        if not value:
            return None
        try:
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _collect_phq_frames(phq_path: Path) -> tuple[dict, list[dict]]:
        """Aggregate PHQ facial analysis frames."""
        if not phq_path.exists():
            return {}, []

        frames: list[dict] = []
        emotion_counts: Counter[str] = Counter()
        au_sums: defaultdict[str, float] = defaultdict(float)
        frame_index = 0

        with phq_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("type") == "metadata":
                    continue

                analysis = entry.get("analysis") or {}
                facial_expression = analysis.get("facial_expression")
                au_intensities = analysis.get("au_intensities") or {}

                frames.append(
                    {
                        "index": frame_index,
                        "timestamp": entry.get("timestamp"),
                        "facial_expression": facial_expression,
                        "au_intensities": au_intensities,
                    }
                )
                frame_index += 1

                if facial_expression:
                    emotion_counts[facial_expression] += 1

                for au, value in au_intensities.items():
                    if isinstance(value, (int, float)):
                        au_sums[au] += float(value)

        if frame_index == 0:
            summary = {
                "frame_count": 0,
                "emotion_distribution": {},
                "average_au_intensities": {},
            }
            return summary, frames

        average_intensities = {
            au: round(total / frame_index, 4) for au, total in au_sums.items()
        }
        summary = {
            "frame_count": frame_index,
            "emotion_distribution": dict(emotion_counts),
            "average_au_intensities": average_intensities,
        }
        return summary, frames

    @classmethod
    def _collect_llm_frames(
        cls,
        llm_path: Path,
        raw_conversation: list[dict],
        llm_metadata: Optional[dict],
    ) -> tuple[dict, list[dict]]:
        """Aggregate LLM facial analysis frames within user timing windows."""
        if not llm_path.exists():
            return {
                "frame_count": 0,
                "emotion_distribution": {},
                "average_au_intensities": {},
                "frames_per_turn": {},
                "used_user_timing": True,
                "note": "analysis_file_missing",
            }, []

        if not isinstance(raw_conversation, list):
            raw_conversation = []

        windows = []
        for turn in raw_conversation:
            if not isinstance(turn, dict):
                continue
            timing = turn.get("user_timing") or {}
            start = timing.get("start")
            end = timing.get("end")
            if start is None or end is None:
                continue
            try:
                start_val = float(start)
                end_val = float(end)
            except (TypeError, ValueError):
                continue
            turn_number = turn.get("turn_number")
            if turn_number is None:
                continue
            if end_val < start_val:
                continue
            windows.append((start_val, end_val, turn_number))

        windows.sort(key=lambda item: item[0])

        start_dt = cls._parse_iso_datetime((llm_metadata or {}).get("started_at"))

        if not windows:
            summary = {
                "frame_count": 0,
                "emotion_distribution": {},
                "average_au_intensities": {},
                "frames_per_turn": {},
                "used_user_timing": True,
                "note": "missing_user_timing_or_start_time",
            }
            return summary, []

        raw_frames: list[dict] = []
        with llm_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                entry = json.loads(line)
                entry_type = entry.get("type")
                if entry_type == "metadata":
                    continue
                if entry_type == "summary":
                    continue
                raw_frames.append(entry)

        total_frames = len(raw_frames)
        if total_frames == 0:
            summary = {
                "frame_count": 0,
                "emotion_distribution": {},
                "average_au_intensities": {},
                "frames_per_turn": {},
                "used_user_timing": True,
                "note": "no_frames_available",
            }
            return summary, []

        parsed_timestamps: list[Optional[datetime]] = []
        has_real_timestamps = False
        for frame in raw_frames:
            ts_value = frame.get("timestamp")
            parsed = cls._parse_iso_datetime(ts_value)
            parsed_timestamps.append(parsed)
            if parsed is not None:
                has_real_timestamps = True

        frames: list[dict] = []
        emotion_counts: Counter[str] = Counter()
        au_sums: defaultdict[str, float] = defaultdict(float)
        frames_per_turn: Counter[int] = Counter()

        def _record_frame(turn_number: int, offset_seconds: float, frame_entry: dict) -> None:
            analysis = frame_entry.get("analysis") or {}
            facial_expression = analysis.get("facial_expression")
            au_intensities = analysis.get("au_intensities") or {}

            frames.append(
                {
                    "turn_number": turn_number,
                    "offset_seconds": round(offset_seconds, 3),
                    "timestamp": frame_entry.get("timestamp"),
                    "facial_expression": facial_expression,
                    "au_intensities": au_intensities,
                }
            )

            if facial_expression:
                emotion_counts[facial_expression] += 1

            for au, value in au_intensities.items():
                if isinstance(value, (int, float)):
                    au_sums[au] += float(value)

            frames_per_turn[turn_number] += 1

        note: Optional[str] = None
        used_sequential = False

        def _assign_frames_sequential() -> None:
            nonlocal used_sequential
            used_sequential = True
            window_starts = [window_start for window_start, _, _ in windows]
            window_ends = [window_end for _, window_end, _ in windows]
            start_min = window_starts[0]
            end_max = max(window_ends)
            if end_max <= start_min:
                end_max = start_min + float(total_frames or 1)

            if total_frames > 1:
                offset_step = (end_max - start_min) / (total_frames - 1)
            else:
                offset_step = 0.0

            window_index = 0
            for idx, frame_entry in enumerate(raw_frames):
                offset_seconds = start_min + offset_step * idx
                while (
                    window_index + 1 < len(windows)
                    and offset_seconds > windows[window_index][1]
                ):
                    window_index += 1
                matched_window = windows[min(window_index, len(windows) - 1)]
                turn_number = matched_window[2]
                _record_frame(turn_number, offset_seconds, frame_entry)

        if has_real_timestamps and start_dt is not None:
            for frame_entry, timestamp_dt in zip(raw_frames, parsed_timestamps):
                if timestamp_dt is None:
                    continue

                offset_seconds = (timestamp_dt - start_dt).total_seconds()
                if offset_seconds < 0:
                    continue

                matched_turn = None
                for window_start, window_end, turn_number in windows:
                    if window_start <= offset_seconds <= window_end:
                        matched_turn = turn_number
                        break

                if matched_turn is None:
                    continue

                _record_frame(matched_turn, offset_seconds, frame_entry)

            if not frames:
                _assign_frames_sequential()
                if frames:
                    note = "timestamp_alignment_failed_used_sequential"
        else:
            _assign_frames_sequential()

        if not frames:
            note = "no_frames_matched_user_timing"

        frame_count = len(frames)
        average_intensities = {
            au: round(total / frame_count, 4) for au, total in au_sums.items()
        } if frame_count else {}

        summary = {
            "frame_count": frame_count,
            "emotion_distribution": dict(emotion_counts),
            "average_au_intensities": average_intensities,
            "frames_per_turn": dict(frames_per_turn),
            "used_user_timing": True,
        }
        if frame_count == 0:
            summary["note"] = "no_frames_matched_user_timing"
        if used_sequential:
            summary["used_sequential_timing"] = True
        if note and (frame_count > 0 or summary.get("note") is None):
            summary["note"] = note

        return summary, frames

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

    @staticmethod
    def _merge_summary_extra(
        summary: Optional[AssessmentSummary], extra: dict
    ) -> Optional[AssessmentSummary]:
        """Merge additional metrics into the AssessmentSummary.extra field."""
        if summary is None or not extra:
            return summary

        current_extra = dict(summary.extra or {})
        current_extra.update(extra)
        return summary.model_copy(update={"extra": current_extra})

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

        # PHQ processing
        phq_summary_dict, phq_frames = self._collect_phq_frames(
            session_folder / "phq_analysis.jsonl"
        )
        if phq_summary_dict:
            phq_summary_path = facial_dir / "phq_summary.json"
            phq_frames_path = facial_dir / "phq_frames.jsonl"
            self._write_json_file(phq_summary_path, phq_summary_dict)
            self._write_jsonl_file(phq_frames_path, phq_frames)

            phq_summary = self._merge_summary_extra(phq_summary, phq_summary_dict)

            facial_meta["phq"] = {
                "summary_file": str(phq_summary_path.relative_to(output_root)),
                "frames_file": str(phq_frames_path.relative_to(output_root)),
            }

        # LLM processing (aligned to user timing)
        llm_summary_dict, llm_frames = self._collect_llm_frames(
            session_folder / "llm_analysis.jsonl",
            metadata.get("raw_conversation") or [],
            (metadata.get("session_metadata") or {}).get("llm_analysis"),
        )
        if llm_summary_dict:
            llm_summary_path = facial_dir / "llm_summary.json"
            llm_frames_path = facial_dir / "llm_frames.jsonl"
            self._write_json_file(llm_summary_path, llm_summary_dict)
            self._write_jsonl_file(llm_frames_path, llm_frames)

            llm_summary = self._merge_summary_extra(llm_summary, llm_summary_dict)

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


def _model_to_dict(model):
    """Return a serialisable representation compatible with Pydantic v1 & v2."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Unsupported model type: {type(model)!r}")
