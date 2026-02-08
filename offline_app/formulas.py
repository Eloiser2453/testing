from __future__ import annotations

from typing import Any, Dict, List

SEGMENT_KEYS: List[str] = [f"seg_{index}" for index in range(1, 7)]
SEGMENT_VALUES = {1, 2, 3, 4}

DEFAULT_DATA: Dict[str, Any] = {
    "patient_name": "",
    "age": "",
    "diagnosis": "",
    "rhythm": "",
}
for key in SEGMENT_KEYS:
    DEFAULT_DATA[key] = None


def _parse_segment(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value if value in SEGMENT_VALUES else None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        parsed = int(text)
        return parsed if parsed in SEGMENT_VALUES else None
    return None


def normalize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, default_value in DEFAULT_DATA.items():
        result[key] = data.get(key, default_value)

    result["patient_name"] = str(result["patient_name"] or "").strip()
    result["age"] = str(result["age"] or "").strip()
    result["diagnosis"] = str(result["diagnosis"] or "").strip()
    result["rhythm"] = str(result["rhythm"] or "").strip()

    for key in SEGMENT_KEYS:
        result[key] = _parse_segment(result.get(key))

    return result


def compute_results(data: Dict[str, Any]) -> Dict[str, Any]:
    segments = [data.get(key) for key in SEGMENT_KEYS]
    filled_segments = [value for value in segments if isinstance(value, int)]
    segment_count = len(filled_segments)
    if segment_count:
        lv_score = round(sum(filled_segments) / segment_count, 2)
        status = "ok"
    else:
        lv_score = 0.0
        status = "missing_segments"

    return {
        "lv_score": lv_score,
        "segment_count": segment_count,
        "status": status,
    }
