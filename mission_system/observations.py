"""Объединение повторных наблюдений одной учебной зоны."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .models import Target


@dataclass(frozen=True)
class Observation:
    observation_id: str
    frame_id: str
    object_class: str
    x: float
    y: float
    score: float


def fuse_observations(
    observations: Iterable[Observation],
    merge_radius_m: float = 0.12,
    minimum_score: float = 0.6,
) -> tuple[Target, ...]:
    """Объединяет близкие наблюдения, а противоречащие классы помечает U."""
    if merge_radius_m <= 0:
        raise ValueError("Радиус объединения должен быть положительным")
    groups: list[list[Observation]] = []
    for observation in observations:
        if observation.object_class not in {"A", "B", "U"}:
            raise ValueError(f"Неизвестный класс {observation.object_class}")
        matching_group = None
        for group in groups:
            center_x = sum(item.x for item in group) / len(group)
            center_y = sum(item.y for item in group) / len(group)
            if math.hypot(observation.x - center_x, observation.y - center_y) <= merge_radius_m:
                matching_group = group
                break
        if matching_group is None:
            groups.append([observation])
        else:
            matching_group.append(observation)

    targets: list[Target] = []
    for index, group in enumerate(groups, start=1):
        reliable = [item for item in group if item.score >= minimum_score]
        classes = {item.object_class for item in reliable}
        if not reliable or len(classes) != 1 or "U" in classes:
            result_class = "U"
            confidence_label = "uncertain"
        else:
            result_class = next(iter(classes))
            confidence_label = "confirmed"
        x = sum(item.x for item in group) / len(group)
        y = sum(item.y for item in group) / len(group)
        targets.append(
            Target(
                target_id=f"T{index}",
                action_id=f"ACT-{index}",
                object_class=result_class,
                x=x,
                y=y,
                confidence_label=confidence_label,
                source_frame_ids=tuple(sorted({item.frame_id for item in group})),
            )
        )
    return tuple(targets)
