from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

from mission_system.models import MissionMap, PolygonZone, Target


BASE_TIME = datetime(2026, 11, 18, 9, 0, tzinfo=timezone.utc)


def make_map(
    targets: tuple[Target, ...] | None = None,
    zones: tuple[PolygonZone, ...] | None = None,
    expires_delta: timedelta = timedelta(minutes=15),
) -> MissionMap:
    if targets is None:
        targets = (
            Target("A1", "ACT-1", "A", 1.0, 0.8, priority=2, source_frame_ids=("F1",)),
            Target("A2", "ACT-2", "A", 1.0, 3.2, priority=1, source_frame_ids=("F2",)),
            Target("A3", "ACT-3", "A", 3.0, 0.5, source_frame_ids=("F3",)),
            Target("A4", "ACT-4", "A", 3.2, 3.5, source_frame_ids=("F4",)),
            Target("A5", "ACT-5", "A", 5.2, 3.3, source_frame_ids=("F5",)),
            Target("A6", "ACT-6", "A", 5.5, 2.6, source_frame_ids=("F6",)),
        )
    if zones is None:
        zones = (
            PolygonZone("NFZ-1", ((2.1, 1.6), (3.1, 1.6), (3.1, 2.6), (2.1, 2.6))),
            PolygonZone("NFZ-2", ((4.1, 1.0), (4.8, 1.0), (4.8, 1.8), (4.1, 1.8))),
        )
    mission_map = MissionMap(
        schema_version="1.0",
        mission_id="MISSION-001",
        frame_id="F",
        units="m",
        calibration_id_recon="RECON-CAL-1",
        calibration_id_executor="EXEC-CAL-1",
        last_source_frame_at=BASE_TIME.isoformat(),
        expires_at=(BASE_TIME + expires_delta).isoformat(),
        field_width=6.0,
        field_height=4.0,
        targets=targets,
        forbidden_zones=zones,
    )
    return mission_map.with_checksum()


def replace_and_sign(mission_map: MissionMap, **changes) -> MissionMap:
    return replace(mission_map, **changes, checksum="").with_checksum()
