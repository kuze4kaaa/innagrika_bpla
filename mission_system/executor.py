"""Автомат исполнителя с непрерывным контролем допуска и защитой от повторов."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any

from .geometry import distance, point_in_polygon
from .models import MissionMap, Target
from .validator import MapValidator, ValidationError


class ExecutorState(str, Enum):
    WAITING = "WAITING"
    VALIDATING = "VALIDATING"
    READY = "READY"
    NAVIGATING = "NAVIGATING"
    STABILIZING = "STABILIZING"
    OPERATING = "OPERATING"
    CONFIRMED = "CONFIRMED"
    SKIPPED = "SKIPPED"
    MAP_ERROR = "MAP_ERROR"
    SAFE_STOP = "SAFE_STOP"


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    z: float
    speed_mps: float
    error_m: float
    measured_at: datetime


class ActionRegistry:
    """Хранит результат action_id между перезапусками программы."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._records: dict[str, str] = {}
        if self.path is not None and self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Файл реестра действий повреждён")
            self._records = {str(key): str(value) for key, value in data.items()}

    def status(self, action_id: str) -> str | None:
        return self._records.get(action_id)

    def is_blocked(self, action_id: str) -> bool:
        return action_id in self._records

    def mark_started(self, action_id: str) -> None:
        if self.is_blocked(action_id):
            raise ValueError(f"Действие {action_id} уже запускалось")
        self._records[action_id] = "STARTED"
        self._save()

    def mark_completed(self, action_id: str) -> None:
        if self._records.get(action_id) != "STARTED":
            raise ValueError("Нельзя подтвердить действие, которое не было запущено")
        self._records[action_id] = "COMPLETED"
        self._save()

    def mark_uncertain(self, action_id: str) -> None:
        if action_id not in self._records:
            self._records[action_id] = "UNCERTAIN"
        elif self._records[action_id] != "COMPLETED":
            self._records[action_id] = "UNCERTAIN"
        self._save()

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(self.path)


class Executor:
    def __init__(
        self,
        validator: MapValidator,
        registry: ActionRegistry,
        log_path: str | Path | None = None,
        position_age_limit_s: float = 0.3,
        position_error_limit_m: float = 0.06,
        target_offset_limit_m: float = 0.06,
        altitude_min_m: float = 1.0,
        altitude_max_m: float = 1.4,
        stable_speed_limit_mps: float = 0.05,
        stabilization_s: float = 1.0,
        operation_s: float = 2.0,
    ) -> None:
        self.validator = validator
        self.registry = registry
        self.log_path = Path(log_path) if log_path is not None else None
        self.position_age_limit_s = position_age_limit_s
        self.position_error_limit_m = position_error_limit_m
        self.target_offset_limit_m = target_offset_limit_m
        self.altitude_min_m = altitude_min_m
        self.altitude_max_m = altitude_max_m
        self.stable_speed_limit_mps = stable_speed_limit_mps
        self.stabilization_s = stabilization_s
        self.operation_s = operation_s

        self.state = ExecutorState.WAITING
        self.mission_map: MissionMap | None = None
        self.target: Target | None = None
        self.led_enabled = False
        self.events: list[dict[str, Any]] = []
        self._last_update_at: datetime | None = None
        self._stable_seconds = 0.0
        self._operation_seconds = 0.0

    def load_map(self, mission_map: MissionMap, now: datetime) -> None:
        self.state = ExecutorState.VALIDATING
        try:
            self.validator.require_valid(mission_map, now=now)
        except ValidationError as error:
            self.state = ExecutorState.MAP_ERROR
            self._log(now, "map_rejected", reason=str(error))
            raise
        self.mission_map = mission_map
        self.target = None
        self.led_enabled = False
        self._stable_seconds = 0.0
        self._operation_seconds = 0.0
        self._last_update_at = now
        self.state = ExecutorState.READY
        self._log(now, "map_accepted")

    def select_target(self, target_id: str, now: datetime) -> None:
        if self.mission_map is None:
            raise RuntimeError("Карта не загружена")
        self.validator.require_valid(self.mission_map, now=now)
        found = next((item for item in self.mission_map.targets if item.target_id == target_id), None)
        if found is None:
            raise ValueError(f"Цель {target_id} отсутствует в карте")
        if self.registry.is_blocked(found.action_id):
            self.state = ExecutorState.SKIPPED
            self._log(
                now,
                "duplicate_blocked",
                target=found,
                reason=f"action_id уже имеет состояние {self.registry.status(found.action_id)}",
            )
            raise ValueError("Повторное выполнение запрещено")
        self.target = found
        self._stable_seconds = 0.0
        self._operation_seconds = 0.0
        self._last_update_at = now
        self.state = ExecutorState.NAVIGATING
        self._log(now, "target_selected", target=found)

    def update(self, pose: Pose, now: datetime) -> ExecutorState:
        if self.mission_map is None or self.target is None:
            raise RuntimeError("Сначала загрузите карту и выберите цель")
        if now.tzinfo is None or pose.measured_at.tzinfo is None:
            return self._safe_stop(now, "время должно содержать часовой пояс", uncertain=self.led_enabled)

        delta = 0.0
        if self._last_update_at is not None:
            delta = max(0.0, (now - self._last_update_at).total_seconds())
        self._last_update_at = now

        try:
            self.validator.require_valid(self.mission_map, now=now)
        except ValidationError as error:
            return self._safe_stop(now, f"карта стала невалидной: {error}", uncertain=self.led_enabled)

        if delta > self.position_age_limit_s:
            if self.led_enabled:
                return self._safe_stop(
                    now,
                    "нет непрерывных проверок допуска дольше 0,3 с",
                    uncertain=True,
                    pose=pose,
                )
            self._stable_seconds = 0.0
            self.state = ExecutorState.NAVIGATING
            self._log(
                now,
                "control_update_gap",
                target=self.target,
                pose=pose,
                permission=False,
                reason="интервал между проверками больше 0,3 с",
            )
            return self.state

        allowed, reason = self._operation_allowed(pose, now)
        if not allowed:
            if self.led_enabled:
                return self._safe_stop(now, reason, uncertain=True, pose=pose)
            self._stable_seconds = 0.0
            self.state = ExecutorState.NAVIGATING
            self._log(now, "permission_denied", target=self.target, pose=pose, reason=reason)
            return self.state

        if self.state in {ExecutorState.NAVIGATING, ExecutorState.STABILIZING}:
            self.state = ExecutorState.STABILIZING
            self._stable_seconds += delta
            self._log(now, "stabilizing", target=self.target, pose=pose, permission=True)
            if self._stable_seconds >= self.stabilization_s - 1e-9:
                try:
                    self.registry.mark_started(self.target.action_id)
                except ValueError as error:
                    return self._safe_stop(now, str(error), uncertain=False, pose=pose)
                self.led_enabled = True
                self._operation_seconds = 0.0
                self.state = ExecutorState.OPERATING
                self._log(now, "led_on", target=self.target, pose=pose, permission=True, actual_activation=True)
            return self.state

        if self.state == ExecutorState.OPERATING:
            self._operation_seconds += delta
            self._log(now, "operating", target=self.target, pose=pose, permission=True, actual_activation=True)
            if self._operation_seconds >= self.operation_s - 1e-9:
                self.led_enabled = False
                self.registry.mark_completed(self.target.action_id)
                self.state = ExecutorState.CONFIRMED
                self._log(now, "operation_confirmed", target=self.target, pose=pose, permission=True, actual_activation=False)
            return self.state

        return self.state

    def lose_control_link(self, now: datetime) -> ExecutorState:
        return self._safe_stop(now, "потеря связи управления", uncertain=self.led_enabled)

    def lose_localization(self, now: datetime) -> ExecutorState:
        return self._safe_stop(now, "потеря свежей локализации", uncertain=self.led_enabled)

    def _operation_allowed(self, pose: Pose, now: datetime) -> tuple[bool, str]:
        assert self.mission_map is not None and self.target is not None
        age = (now - pose.measured_at).total_seconds()
        if age < 0:
            return False, "измерение положения имеет время из будущего"
        if age > self.position_age_limit_s:
            return False, "возраст положения больше 0,3 с"
        if pose.error_m > self.position_error_limit_m or pose.error_m < 0:
            return False, "оценка ошибки положения превышает 0,06 м"
        if not (self.altitude_min_m <= pose.z <= self.altitude_max_m):
            return False, "высота вне коридора 1,0-1,4 м"
        if pose.speed_mps < 0 or pose.speed_mps > self.stable_speed_limit_mps:
            return False, "БПЛА не находится устойчиво над целью"
        if distance((pose.x, pose.y), (self.target.x, self.target.y)) > self.target_offset_limit_m:
            return False, "смещение от центра цели больше 0,06 м"
        if not (0.0 <= pose.x <= self.mission_map.field_width and 0.0 <= pose.y <= self.mission_map.field_height):
            return False, "положение вне поля"
        if any(point_in_polygon((pose.x, pose.y), zone.vertices) for zone in self.mission_map.forbidden_zones):
            return False, "положение в запретной зоне"
        return True, ""

    def _safe_stop(
        self,
        now: datetime,
        reason: str,
        uncertain: bool,
        pose: Pose | None = None,
    ) -> ExecutorState:
        if self.target is not None and uncertain:
            self.registry.mark_uncertain(self.target.action_id)
        self.led_enabled = False
        self.state = ExecutorState.SAFE_STOP
        self._log(now, "safe_stop", target=self.target, pose=pose, permission=False, actual_activation=False, reason=reason)
        return self.state

    def _log(
        self,
        now: datetime,
        event: str,
        target: Target | None = None,
        pose: Pose | None = None,
        permission: bool | None = None,
        actual_activation: bool | None = None,
        reason: str = "",
    ) -> None:
        item: dict[str, Any] = {
            "time": now.astimezone(timezone.utc).isoformat(),
            "mission_id": self.mission_map.mission_id if self.mission_map else None,
            "target_id": target.target_id if target else None,
            "action_id": target.action_id if target else None,
            "state": self.state.value,
            "event": event,
            "permission": permission,
            "actual_activation": actual_activation,
            "reason": reason,
        }
        if pose is not None:
            item["pose"] = {
                "x": pose.x,
                "y": pose.y,
                "z": pose.z,
                "speed_mps": pose.speed_mps,
                "error_m": pose.error_m,
                "measured_at": pose.measured_at.astimezone(timezone.utc).isoformat(),
            }
        self.events.append(item)
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
