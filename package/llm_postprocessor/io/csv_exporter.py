"""CSV export utilities for analysis results."""

import csv
import json
from pathlib import Path
from typing import Optional


class CSVExporter:
    """Export analysis results to CSV files."""

    @staticmethod
    def export_llm_facial_analysis(
        post_processed_folder: str | Path,
        output_file: str | Path = "llm_facial_analysis.csv"
    ) -> dict:
        """Export LLM facial analysis to CSV.

        Args:
            post_processed_folder: Path to post_processed folder
            output_file: Output CSV filename

        Returns:
            Stats dict with count of exported rows
        """
        post_processed_path = Path(post_processed_folder)
        output_path = Path(output_file)

        rows = []

        for result_file in sorted(post_processed_path.glob("*/analysis_result.json")):
            with open(result_file, "r") as f:
                data = json.load(f)

            user_id = data.get("user_id")
            session_id = data.get("session_id")

            llm_summary = data.get("llm_summary", {})
            llm_extra = llm_summary.get("extra", {}) if llm_summary else {}

            frame_count = llm_extra.get("frame_count", 0)
            emotion_dist = llm_extra.get("emotion_distribution", {})
            avg_au = llm_extra.get("average_au_intensities", {})
            frames_per_turn = llm_extra.get("frames_per_turn", {})

            dominant_emotion = max(emotion_dist.items(), key=lambda x: x[1])[0] if emotion_dist else None

            row = {
                "user_id": user_id,
                "session_id": session_id,
                "frame_count": frame_count,
                "dominant_emotion": dominant_emotion,
                "emotion_distribution": json.dumps(emotion_dist),
                "avg_au_intensities": json.dumps(avg_au),
                "frames_per_turn": json.dumps(frames_per_turn),
            }
            rows.append(row)

        if rows:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return {"exported": len(rows), "output_file": str(output_path)}

    @staticmethod
    def export_phq_facial_analysis(
        post_processed_folder: str | Path,
        output_file: str | Path = "phq_facial_analysis.csv"
    ) -> dict:
        """Export PHQ facial analysis to CSV.

        Args:
            post_processed_folder: Path to post_processed folder
            output_file: Output CSV filename

        Returns:
            Stats dict with count of exported rows
        """
        post_processed_path = Path(post_processed_folder)
        output_path = Path(output_file)

        rows = []

        for result_file in sorted(post_processed_path.glob("*/analysis_result.json")):
            with open(result_file, "r") as f:
                data = json.load(f)

            user_id = data.get("user_id")
            session_id = data.get("session_id")

            phq_summary = data.get("phq_summary", {})
            phq_extra = phq_summary.get("extra", {}) if phq_summary else {}

            frame_count = phq_extra.get("frame_count", 0)
            emotion_dist = phq_extra.get("emotion_distribution", {})
            avg_au = phq_extra.get("average_au_intensities", {})

            dominant_emotion = max(emotion_dist.items(), key=lambda x: x[1])[0] if emotion_dist else None

            row = {
                "user_id": user_id,
                "session_id": session_id,
                "frame_count": frame_count,
                "dominant_emotion": dominant_emotion,
                "emotion_distribution": json.dumps(emotion_dist),
                "avg_au_intensities": json.dumps(avg_au),
            }
            rows.append(row)

        if rows:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return {"exported": len(rows), "output_file": str(output_path)}

    @staticmethod
    def export_llm_evaluation_results(
        post_processed_folder: str | Path,
        output_folder: str | Path = "csv_exports"
    ) -> dict:
        """Export LLM evaluation results to separate CSV per model.

        Args:
            post_processed_folder: Path to post_processed folder containing evaluations subfolders
            output_folder: Output folder for CSV files

        Returns:
            Stats dict with count of exported rows per model
        """
        post_processed_path = Path(post_processed_folder)
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        model_data = {}

        for session_folder in sorted(post_processed_path.glob("*_session*")):
            evaluations_folder = session_folder / "evaluations"
            if not evaluations_folder.exists():
                continue

            folder_name = session_folder.name
            parts = folder_name.rsplit("_", 1)
            session_id = parts[-1] if len(parts) > 1 else "session1"
            user_id = parts[0] if len(parts) > 1 else folder_name

            for model_folder in evaluations_folder.iterdir():
                if not model_folder.is_dir():
                    continue

                eval_file = model_folder / "evaluation.json"
                if not eval_file.exists():
                    continue

                model_name = model_folder.name

                if model_name not in model_data:
                    model_data[model_name] = []

                with open(eval_file, "r") as f:
                    data = json.load(f)

                response = data.get("response", {})
                analysis = response.get("analysis", [])
                totals = response.get("totals", {})
                notes = response.get("notes", "")

                row = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "phq_sum": totals.get("phq_sum", 0),
                    "notes": notes,
                }

                for item in analysis:
                    indicator = item.get("indicator", "")
                    context = item.get("context", "")
                    score = item.get("score", {}).get("phq", 0)

                    row[f"{indicator}_score"] = score
                    row[f"{indicator}_context"] = context

                model_data[model_name].append(row)

        stats = {}

        for model_name, rows in model_data.items():
            if not rows:
                continue

            safe_model_name = model_name.replace("/", "_").replace(".", "_")
            output_file = output_path / f"llm_evaluation_{safe_model_name}.csv"

            fieldnames = set()
            for row in rows:
                fieldnames.update(row.keys())

            fieldnames = ["user_id", "session_id", "phq_sum"] + sorted([f for f in fieldnames if f not in ["user_id", "session_id", "phq_sum", "notes"]]) + ["notes"]

            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            stats[model_name] = {"exported": len(rows), "output_file": str(output_file)}

        return stats

    @staticmethod
    def export_phq_scores(
        post_processed_folder: str | Path,
        output_file: str | Path = "phq_scores.csv"
    ) -> dict:
        """Export PHQ scores to CSV.

        Args:
            post_processed_folder: Path to post_processed folder
            output_file: Output CSV filename

        Returns:
            Stats dict with count of exported rows
        """
        post_processed_path = Path(post_processed_folder)
        output_path = Path(output_file)

        rows = []

        for result_file in sorted(post_processed_path.glob("*/analysis_result.json")):
            with open(result_file, "r") as f:
                data = json.load(f)

            user_id = data.get("user_id")
            session_id = data.get("session_id")

            phq_summary = data.get("phq_summary", {})
            phq_extra = phq_summary.get("extra", {}) if phq_summary else {}

            total_score = phq_extra.get("total_score", 0)
            max_score = phq_extra.get("max_possible_score", 27)
            responses = phq_extra.get("responses", {})

            severity = "none"
            if total_score >= 20:
                severity = "severe"
            elif total_score >= 15:
                severity = "moderately_severe"
            elif total_score >= 10:
                severity = "moderate"
            elif total_score >= 5:
                severity = "mild"

            row = {
                "user_id": user_id,
                "session_id": session_id,
                "total_score": total_score,
                "max_possible_score": max_score,
                "severity_level": severity,
            }

            for i in range(1, 10):
                q_key = f"Q{i}"
                row[q_key] = responses.get(q_key, 0) if responses else 0

            rows.append(row)

        if rows:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return {"exported": len(rows), "output_file": str(output_path)}

    @classmethod
    def export_all(
        cls,
        post_processed_folder: str | Path = "post_processed",
        output_folder: str | Path = "csv_exports"
    ) -> dict:
        """Export all CSV files.

        Args:
            post_processed_folder: Path to post_processed folder
            output_folder: Output folder for CSV files

        Returns:
            Stats dict with all export results
        """
        output_path = Path(output_folder)
        output_path.mkdir(parents=True, exist_ok=True)

        stats = {}

        stats["llm_facial"] = cls.export_llm_facial_analysis(
            post_processed_folder,
            output_path / "llm_facial_analysis.csv"
        )

        stats["phq_facial"] = cls.export_phq_facial_analysis(
            post_processed_folder,
            output_path / "phq_facial_analysis.csv"
        )

        stats["phq_scores"] = cls.export_phq_scores(
            post_processed_folder,
            output_path / "phq_scores.csv"
        )

        stats["llm_evaluation"] = cls.export_llm_evaluation_results(
            post_processed_folder,
            output_path
        )

        return stats
