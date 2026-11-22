"""Уровневая система: уровень L требует (L-1)^2 * 100 баллов.

0 → 1, 100 → 2, 400 → 3, 900 → 4, 1600 → 5, ...
"""

import math


def level_for_points(points: int) -> int:
    return 1 + math.floor(math.sqrt(max(0, points) / 100))


def rank_title(level: int) -> str:
    if level >= 6:
        return "Хранитель планеты"
    if level >= 4:
        return "Эко-боец"
    if level >= 2:
        return "Активист"
    return "Новичок"


def level_progress(points: int) -> dict:
    """Прогресс до следующего уровня: progress ∈ [0, 1]."""
    level = level_for_points(points)
    prev_level_at = (level - 1) ** 2 * 100
    next_level_at = level**2 * 100
    span = next_level_at - prev_level_at
    progress = 1.0 if span == 0 else min(1.0, (points - prev_level_at) / span)
    return {
        "level": level,
        "current": points,
        "nextLevelAt": next_level_at,
        "progress": round(progress, 4),
    }
