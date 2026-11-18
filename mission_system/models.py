"""Структуры карты наблюдений и карты-задания."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable


ALLOWED_CLASSES = {"A", "B", "U"}


def parse_time(value: str) -> datetime:
    """Разбирает время ISO 8601 и возвращает значение с часовым поясом."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Время должно содержать часовой пояс")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class Target:
    target_id: str
    action_id: str
    object_class: str
    x: float
    y: float
    confidence_label: str = "confirmed"
    priority: int = 0
    source_frame_ids: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Target":
        return cls(
            target_id=str(data["target_id"]),
            action_id=str(data["action_id"]),
            object_class=str(data["class"]),
            x=float(data["x"]),
            y=float(data["y"]),
            confidence_label=str(data.get("confidence_label", "confirmed")),
            priority=int(data.get("priority", 0)),
            source_frame_ids=tuple(str(item) for item in data.get("source_frame_ids", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "action_id": self.action_id,
            "class": self.object_class,
            "x": self.x,
            "y": self.y,
            "confidence_label": self.confidence_label,
            "priority": self.priority,
            "source_frame_ids": list(self.source_frame_ids),
        }


@dataclass(frozen=True)
class PolygonZone:
    zone_id: str
    vertices: tuple[tuple[float, float], ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolygonZone":
        vertices = tuple((float(point[0]), float(point[1])) for point in data["vertices"])
        return cls(zone_id=str(data["zone_id"]), vertices=vertices)

    def to_dict(self) -> dict[str, Any]:
        return {"zone_id": self.zone_id, "vertices": [list(point) for point in self.vertices]}


@dataclass(frozen=True)
class MissionMap:
    schema_version: str
    mission_id: str
    frame_id: str
    units: str
    calibration_id_recon: str
    calibration_id_executor: str
    last_source_frame_at: str
    expires_at: str
    field_width: float
    field_height: float
    targets: tuple[Target, ...] = field(default_factory=tuple)
    forbidden_zones: tuple[PolygonZone, ...] = field(default_factory=tuple)
    checksum: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MissionMap":
        field_data = data["field"]
        return cls(
            schema_version=str(data["schema_version"]),
            mission_id=str(data["mission_id"]),
            frame_id=str(data["frame_id"]),
            units=str(data["units"]),
            calibration_id_recon=str(data["calibration_id_recon"]),
            calibration_id_executor=str(data["calibration_id_executor"]),
            last_source_frame_at=str(data["last_source_frame_at"]),
            expires_at=str(data["expires_at"]),
            field_width=float(field_data["width"]),
            field_height=float(field_data["height"]),
            targets=tuple(Target.from_dict(item) for item in data.get("targets", [])),
            forbidden_zones=tuple(PolygonZone.from_dict(item) for item in data.get("forbidden_zones", [])),
            checksum=str(data.get("checksum", "")),
        )

    @classmethod
    def from_json(cls, text: str) -> "MissionMap":
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("Корень карты должен быть объектом JSON")
        return cls.from_dict(data)

    def to_dict(self, include_checksum: bool = True) -> dict[str, Any]:
        result = {
            "schema_version": self.schema_version,
            "mission_id": self.mission_id,
            "frame_id": self.frame_id,
            "units": self.units,
            "calibration_id_recon": self.calibration_id_recon,
            "calibration_id_executor": self.calibration_id_executor,
            "last_source_frame_at": self.last_source_frame_at,
            "expires_at": self.expires_at,
            "field": {"width": self.field_width, "height": self.field_height},
            "targets": [target.to_dict() for target in self.targets],
            "forbidden_zones": [zone.to_dict() for zone in self.forbidden_zones],
        }
        if include_checksum:
            result["checksum"] = self.checksum
        return result

    def canonical_payload(self) -> str:
        return json.dumps(
            self.to_dict(include_checksum=False),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def calculated_checksum(self) -> str:
        return sha256(self.canonical_payload().encode("utf-8")).hexdigest()

    def with_checksum(self) -> "MissionMap":
        data = self.to_dict(include_checksum=False)
        data["checksum"] = self.calculated_checksum()
        return MissionMap.from_dict(data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def make_task_targets(observations: Iterable[Target]) -> tuple[Target, ...]:
    """Формирует карту-задание только из подтверждённых объектов класса A."""
    return tuple(
        target
        for target in observations
        if target.object_class == "A" and target.confidence_label == "confirmed"
    )
