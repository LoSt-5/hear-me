"""Сбор кадров в сессию записи и распознавание фразы после остановки."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

IGNORE = {"", "no"}

if TYPE_CHECKING:
    from utils import SLInference


def collapse_runs(gestures: Iterable[str]) -> list[str]:
    out: list[str] = []
    for g in gestures:
        if g in IGNORE:
            continue
        if not out or out[-1] != g:
            out.append(g)
    return out


def scan_frames(frames: list, inference: "SLInference") -> list[str]:
    """Скользящее окно по записанным кадрам → последовательность жестов."""
    if not frames:
        return []

    window = inference.config["window_size"]
    stride = max(1, window // 4)
    raw: list[str] = []

    if len(frames) < window:
        clip = list(frames)
        while len(clip) < window:
            clip.append(frames[-1])
        pred = inference.model.predict(clip[-window:])
        if pred:
            raw.append(pred["labels"][0])
    else:
        for start in range(0, len(frames) - window + 1, stride):
            clip = frames[start : start + window]
            pred = inference.model.predict(list(clip))
            if pred:
                raw.append(pred["labels"][0])

    return collapse_runs(raw)


def build_phrase(gestures: list[str]) -> str:
    return " ".join(gestures).strip()
