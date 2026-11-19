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
    print("Таблица расстояний по безопасным переходам, м:")
    labels = plan.distance_table_points
    width = max(8, *(len(label) + 1 for label in labels))
    print(" " * width + "".join(f"{label:>{width}}" for label in labels))
    for label, row in zip(labels, plan.distance_table_m):
        print(f"{label:>{width}}" + "".join(f"{length:{width}.2f}" for length in row))
    print(f"Порядок целей: {', '.join(plan.target_ids) or 'нет допустимых целей'}")
    print(f"Длина маршрута с возвратом: {plan.route_length_m:.2f} м")
    if plan.nearest_route_length_m is not None:
        print(f"Маршрут по ближайшей цели (все достижимые цели): {plan.nearest_route_length_m:.2f} м")
    print(f"Расчётное время с резервом: {plan.estimated_total_seconds:.1f} с")
    if plan.skipped:
        print("Пропуски:")
        for target_id, reason in plan.skipped:
            print(f"  {target_id}: {reason}")


if __name__ == "__main__":
    main()
