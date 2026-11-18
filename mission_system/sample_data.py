"""Воспроизводимый пример карты для демонстрации безопасного ядра."""

from datetime import datetime, timedelta, timezone

from .models import MissionMap, PolygonZone, Target


def build_example_map(now: datetime | None = None) -> MissionMap:
    last_frame = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    mission_map = MissionMap(
        schema_version="1.0",
        mission_id="AT11-2-DEMO",
        frame_id="F",
        units="m",
        calibration_id_recon="RECON-UWB-CAL-1",
        calibration_id_executor="EXEC-UWB-CAL-1",
        last_source_frame_at=last_frame.isoformat(),
        expires_at=(last_frame + timedelta(minutes=15)).isoformat(),
        field_width=6.0,
        field_height=4.0,
        targets=(
            Target("A1", "AT11-2-DEMO-A1", "A", 1.0, 0.8, priority=2, source_frame_ids=("FRAME-01",)),
            Target("A2", "AT11-2-DEMO-A2", "A", 1.0, 3.2, priority=1, source_frame_ids=("FRAME-02",)),
            Target("A3", "AT11-2-DEMO-A3", "A", 3.0, 0.5, source_frame_ids=("FRAME-03",)),
            Target("A4", "AT11-2-DEMO-A4", "A", 3.2, 3.5, source_frame_ids=("FRAME-04",)),
            Target("A5", "AT11-2-DEMO-A5", "A", 5.2, 3.3, source_frame_ids=("FRAME-05",)),
            Target("A6", "AT11-2-DEMO-A6", "A", 5.5, 2.6, source_frame_ids=("FRAME-06",)),
        ),
        forbidden_zones=(
            PolygonZone("NFZ-1", ((2.1, 1.6), (3.1, 1.6), (3.1, 2.6), (2.1, 2.6))),
            PolygonZone("NFZ-2", ((4.1, 1.0), (4.8, 1.0), (4.8, 1.8), (4.1, 1.8))),
        ),
    )
    return mission_map.with_checksum()
