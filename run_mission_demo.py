"""Проверка карты и расчёт безопасного маршрута на примере АТ11-2."""

from datetime import datetime, timezone

from mission_system.planner import MissionPlanner
from mission_system.sample_data import build_example_map
from mission_system.validator import MapValidator


def main() -> None:
    now = datetime.now(timezone.utc)
    mission_map = build_example_map(now)
    validator = MapValidator({"RECON-UWB-CAL-1"}, {"EXEC-UWB-CAL-1"})
    validator.require_valid(mission_map, now=now)

    plan = MissionPlanner().plan(mission_map)
    print("Карта прошла проверку")
    print(f"Метод: {plan.method}")
    print(f"Порядок целей: {', '.join(plan.target_ids) or 'нет допустимых целей'}")
    print(f"Длина маршрута с возвратом: {plan.route_length_m:.2f} м")
    print(f"Расчётное время с резервом: {plan.estimated_total_seconds:.1f} с")
    if plan.skipped:
        print("Пропуски:")
        for target_id, reason in plan.skipped:
            print(f"  {target_id}: {reason}")


if __name__ == "__main__":
    main()
