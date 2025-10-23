"""Facial analysis aggregation and processing."""

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..schemas.output_schemas import AssessmentSummary


class FacialAnalyzer:
    """Aggregate and analyze facial expression data from PHQ and LLM analysis files."""

    @staticmethod
    def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
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
    def collect_phq_frames(phq_path: Path) -> tuple[dict, list[dict]]:
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
    def collect_llm_frames(
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

        start_dt = cls.parse_iso_datetime((llm_metadata or {}).get("started_at"))

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
            parsed = cls.parse_iso_datetime(ts_value)
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
    def merge_summary_extra(
        summary: Optional[AssessmentSummary], extra: dict
    ) -> Optional[AssessmentSummary]:
        """Merge additional metrics into the AssessmentSummary.extra field."""
        if summary is None or not extra:
            return summary

        current_extra = dict(summary.extra or {})
        current_extra.update(extra)
        return summary.model_copy(update={"extra": current_extra})
