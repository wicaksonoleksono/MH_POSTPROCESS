"""Utility helper functions."""

import json
from pathlib import Path
from typing import Any
from collections import Counter, defaultdict


def ensure_dir(path: str | Path) -> Path:
    """Ensure directory exists.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_all_json_files(directory: str | Path, recursive: bool = True) -> list[Path]:
    """Get all JSON files in directory.

    Args:
        directory: Directory path
        recursive: Whether to search recursively

    Returns:
        List of Path objects
    """
    directory = Path(directory)
    pattern = "**/*.json" if recursive else "*.json"
    return sorted(directory.glob(pattern))


def flatten_dict(data: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dictionary.

    Args:
        data: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_phq_severity(score: int) -> str:
    """Get PHQ-9 severity level from score.

    Args:
        score: Total PHQ-9 score (0-27)

    Returns:
        Severity level string
    """
    if score <= 4:
        return "minimal"
    elif score <= 9:
        return "mild"
    elif score <= 14:
        return "moderate"
    elif score <= 19:
        return "moderately_severe"
    else:
        return "severe"


def calculate_emotion_stats(
    frames: list[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, float]]:
    """Calculate emotion frequency and intensity means from frames.

    Args:
        frames: List of facial analysis frames

    Returns:
        Tuple of (emotion_frequency, emotion_intensity_mean)
    """
    emotion_counts = Counter()
    emotion_intensities = defaultdict(list)

    for frame in frames:
        if "facial_expression" in frame:
            emotion = frame["facial_expression"]
            emotion_counts[emotion] += 1

            # Extract mean intensity from au_intensities
            if "au_intensities" in frame and isinstance(frame["au_intensities"], dict):
                intensities = list(frame["au_intensities"].values())
                if intensities:
                    mean_intensity = sum(intensities) / len(intensities)
                    emotion_intensities[emotion].append(mean_intensity)

    # Calculate means
    emotion_intensity_mean = {
        emotion: sum(intensities) / len(intensities)
        for emotion, intensities in emotion_intensities.items()
        if intensities
    }

    return dict(emotion_counts), emotion_intensity_mean
