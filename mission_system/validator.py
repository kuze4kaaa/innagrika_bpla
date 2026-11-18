"""Строгая проверка карты-задания перед стартом и перед каждой операцией."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import math
from typing import Iterable

from .geometry import point_in_polygon
from .models import ALLOWED_CLASSES, MissionMap, parse_time


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]


class MapValidator:
    def __init__(
        self,
        known_recon_calibrations: Iterable[str],
        known_executor_calibrations: Iterable[str],
        expected_schema_version: str = "1.0",
        expected_frame_id: str = "F",
        expected_units: str = "m",
        expected_field_width: float = 6.0,
        expected_field_height: float = 4.0,
        maximum_lifetime: timedelta = timedelta(minutes=15),
    ) -> None:
        self.known_recon_calibrations = set(known_recon_calibrations)
        self.known_executor_calibrations = set(known_executor_calibrations)
        self.expected_schema_version = expected_schema_version
        self.expected_frame_id = expected_frame_id
        self.expected_units = expected_units
        self.expected_field_width = expected_field_width
        self.expected_field_height = expected_field_height
        self.maximum_lifetime = maximum_lifetime

    def validate(self, mission_map: MissionMap, now: datetime | None = None) -> ValidationResult:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        errors: list[str] = []

        if mission_map.schema_version != self.expected_schema_version:
            errors.append("неподдерживаемая версия схемы")
        if mission_map.frame_id != self.expected_frame_id:
            errors.append("неизвестная система координат")
        if mission_map.units != self.expected_units:
            errors.append("единицы должны быть указаны как m; автопересчёт запрещён")
        if mission_map.calibration_id_recon not in self.known_recon_calibrations:
            errors.append("неизвестная калибровка разведчика")
        if mission_map.calibration_id_executor not in self.known_executor_calibrations:
            errors.append("неизвестная калибровка исполнителя")
        if not mission_map.mission_id.strip():
            errors.append("не указан идентификатор миссии")
        if mission_map.field_width <= 0 or mission_map.field_height <= 0:
            errors.append("размеры поля должны быть положительными")
        elif not (
            math.isclose(mission_map.field_width, self.expected_field_width)
            and math.isclose(mission_map.field_height, self.expected_field_height)
        ):
            errors.append("размер поля не совпадает с полигоном 6 на 4 м")

        try:
            last_frame = parse_time(mission_map.last_source_frame_at)
            expires = parse_time(mission_map.expires_at)
            if expires - last_frame > self.maximum_lifetime:
                errors.append("срок действия превышает 15 минут от последнего использованного кадра")
            if expires <= last_frame:
                errors.append("срок действия должен быть позже последнего кадра")
            if last_frame > current:
                errors.append("последний использованный кадр имеет время из будущего")
            if current >= expires:
                errors.append("карта просрочена")
        except (ValueError, TypeError):
            errors.append("время карты задано неверно или без часового пояса")

        if not mission_map.checksum:
            errors.append("нет контрольной суммы")
        elif mission_map.checksum != mission_map.calculated_checksum():
            errors.append("контрольная сумма не совпадает")

        target_ids: set[str] = set()
        action_ids: set[str] = set()
        for target in mission_map.targets:
            if not target.target_id.strip():
                errors.append("пустой target_id")
            if not target.action_id.strip():
                errors.append(f"у цели {target.target_id} пустой action_id")
            if target.target_id in target_ids:
                errors.append(f"дублируется target_id {target.target_id}")
            target_ids.add(target.target_id)
            if target.action_id in action_ids:
                errors.append(f"дублируется action_id {target.action_id}")
            action_ids.add(target.action_id)
            if target.object_class not in ALLOWED_CLASSES:
                errors.append(f"неизвестный класс {target.object_class}")
            if target.object_class != "A":
                errors.append(f"в карте-задании есть объект не класса A: {target.target_id}")
            if target.confidence_label != "confirmed":
                errors.append(f"сомнительная цель не допускается: {target.target_id}")
            if not target.source_frame_ids:
                errors.append(f"для цели {target.target_id} не указан исходный кадр")
            if not math.isfinite(target.x) or not math.isfinite(target.y):
                errors.append(f"координаты цели {target.target_id} не являются конечными числами")
            elif not (0.0 <= target.x <= mission_map.field_width and 0.0 <= target.y <= mission_map.field_height):
                errors.append(f"цель {target.target_id} вне границ поля")

        zone_ids: set[str] = set()
        for zone in mission_map.forbidden_zones:
            if zone.zone_id in zone_ids:
                errors.append(f"дублируется запретная зона {zone.zone_id}")
            zone_ids.add(zone.zone_id)
            if len(zone.vertices) < 3:
                errors.append(f"у зоны {zone.zone_id} меньше трёх вершин")
            for vertex in zone.vertices:
                if not all(math.isfinite(value) for value in vertex):
                    errors.append(f"у зоны {zone.zone_id} некорректная вершина")
                elif not (
                    0.0 <= vertex[0] <= mission_map.field_width
                    and 0.0 <= vertex[1] <= mission_map.field_height
                ):
                    errors.append(f"зона {zone.zone_id} выходит за границы поля")

        for target in mission_map.targets:
            if any(point_in_polygon((target.x, target.y), zone.vertices) for zone in mission_map.forbidden_zones):
                errors.append(f"цель {target.target_id} находится в запретной зоне")

        return ValidationResult(valid=not errors, errors=tuple(errors))

    def require_valid(self, mission_map: MissionMap, now: datetime | None = None) -> None:
        result = self.validate(mission_map, now=now)
        if not result.valid:
            raise ValidationError("; ".join(result.errors))
