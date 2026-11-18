"""Планирование безопасного маршрута с возвратом и резервом времени."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import heapq
import itertools
import math
from typing import Iterable, Sequence

from .geometry import clearance_to_polygon, distance, segment_is_safe
from .models import MissionMap, Target


Point = tuple[float, float]


@dataclass(frozen=True)
class PlannedTarget:
    target: Target
    path_to_target: tuple[Point, ...]


@dataclass(frozen=True)
class MissionPlan:
    method: str
    targets: tuple[PlannedTarget, ...]
    return_path: tuple[Point, ...]
    route_length_m: float
    estimated_total_seconds: float
    skipped: tuple[tuple[str, str], ...]

    @property
    def target_ids(self) -> tuple[str, ...]:
        return tuple(item.target.target_id for item in self.targets)


class NoSafePathError(ValueError):
    pass


class MissionPlanner:
    def __init__(
        self,
        clearance_m: float = 0.23,
        grid_resolution_m: float = 0.05,
        planning_speed_mps: float = 0.25,
        stabilization_seconds: float = 1.0,
        action_seconds: float = 2.0,
        takeoff_landing_seconds: float = 30.0,
        reserve_seconds: float = 60.0,
        execution_limit_seconds: float = 360.0,
    ) -> None:
        if clearance_m < 0 or grid_resolution_m <= 0 or planning_speed_mps <= 0:
            raise ValueError("Параметры планировщика должны быть положительными")
        self.clearance_m = clearance_m
        self.grid_resolution_m = grid_resolution_m
        self.planning_speed_mps = planning_speed_mps
        self.stabilization_seconds = stabilization_seconds
        self.action_seconds = action_seconds
        self.takeoff_landing_seconds = takeoff_landing_seconds
        self.reserve_seconds = reserve_seconds
        self.execution_limit_seconds = execution_limit_seconds

    def plan(self, mission_map: MissionMap, home: Point = (0.4, 1.2)) -> MissionPlan:
        targets = tuple(mission_map.targets)
        polygons = tuple(zone.vertices for zone in mission_map.forbidden_zones)
        unreachable: list[tuple[str, str]] = []
        reachable: list[Target] = []

        for target in targets:
            point = (target.x, target.y)
            if any(clearance_to_polygon(point, polygon) < self.clearance_m for polygon in polygons):
                unreachable.append((target.target_id, "цель попала в расширенную запретную зону"))
            else:
                try:
                    self._shortest_path(home, point, mission_map)
                except NoSafePathError:
                    unreachable.append((target.target_id, "нет безопасного пути с возвратом"))
                else:
                    reachable.append(target)

        if not reachable:
            return MissionPlan(
                method="нет допустимых целей",
                targets=(),
                return_path=(home,),
                route_length_m=0.0,
                estimated_total_seconds=self.takeoff_landing_seconds + self.reserve_seconds,
                skipped=tuple(unreachable),
            )

        nearest_order = self._nearest_neighbor_order(reachable, home, mission_map)
        nearest_length = self._order_length(nearest_order, home, mission_map)

        if len(reachable) <= 8:
            exact_order = self._exact_order(reachable, home, mission_map)
            exact_length = self._order_length(exact_order, home, mission_map)
        else:
            exact_order = nearest_order
            exact_length = nearest_length

        full_order = exact_order if exact_length <= nearest_length else nearest_order
        full_method = "точный перебор" if full_order == exact_order and len(reachable) <= 8 else "ближайшая цель"
        full_duration = self._estimate_duration(
            self._order_length(full_order, home, mission_map), len(full_order)
        )

        if full_duration <= self.execution_limit_seconds:
            selected = full_order
            skipped = unreachable
            method = f"{full_method}; сравнение с методом ближайшей цели выполнено"
        else:
            selected = self._best_feasible_subset(reachable, home, mission_map)
            selected_ids = {target.target_id for target in selected}
            skipped = unreachable + [
                (target.target_id, "не помещается во время с возвратом и резервом")
                for target in reachable
                if target.target_id not in selected_ids
            ]
            method = "выполнимое подмножество по приоритету и числу целей"

        return self._build_plan(selected, home, mission_map, method, skipped)

    def _estimate_duration(self, route_length: float, target_count: int) -> float:
        return (
            route_length / self.planning_speed_mps
            + target_count * (self.stabilization_seconds + self.action_seconds)
            + self.takeoff_landing_seconds
            + self.reserve_seconds
        )

    def _nearest_neighbor_order(
        self, targets: Sequence[Target], home: Point, mission_map: MissionMap
    ) -> tuple[Target, ...]:
        remaining = list(targets)
        current = home
        result: list[Target] = []
        while remaining:
            target = min(
                remaining,
                key=lambda item: self._path_length(
                    self._shortest_path(current, (item.x, item.y), mission_map),
                    start=current,
                ),
            )
            remaining.remove(target)
            result.append(target)
            current = (target.x, target.y)
        return tuple(result)

    def _exact_order(
        self, targets: Sequence[Target], home: Point, mission_map: MissionMap
    ) -> tuple[Target, ...]:
        best_order: tuple[Target, ...] | None = None
        best_length = math.inf
        for order in itertools.permutations(targets):
            length = self._order_length(order, home, mission_map)
            if length < best_length:
                best_length = length
                best_order = order
        if best_order is None:
            raise NoSafePathError("Не найден порядок целей")
        return best_order

    def _best_feasible_subset(
        self, targets: Sequence[Target], home: Point, mission_map: MissionMap
    ) -> tuple[Target, ...]:
        best_order: tuple[Target, ...] = ()
        best_score = (-1, -1, -math.inf)
        for count in range(1, len(targets) + 1):
            for subset in itertools.combinations(targets, count):
                order = self._exact_order(subset, home, mission_map) if count <= 8 else self._nearest_neighbor_order(subset, home, mission_map)
                length = self._order_length(order, home, mission_map)
                duration = self._estimate_duration(length, len(order))
                if duration > self.execution_limit_seconds:
                    continue
                score = (sum(target.priority for target in order), len(order), -duration)
                if score > best_score:
                    best_score = score
                    best_order = order
        return best_order

    def _order_length(
        self, order: Sequence[Target], home: Point, mission_map: MissionMap
    ) -> float:
        current = home
        total = 0.0
        for target in order:
            path = self._shortest_path(current, (target.x, target.y), mission_map)
            total += self._path_length(path, start=current)
            current = (target.x, target.y)
        return_path = self._shortest_path(current, home, mission_map)
        total += self._path_length(return_path, start=current)
        return total

    def _build_plan(
        self,
        order: Sequence[Target],
        home: Point,
        mission_map: MissionMap,
        method: str,
        skipped: Iterable[tuple[str, str]],
    ) -> MissionPlan:
        current = home
        planned: list[PlannedTarget] = []
        total = 0.0
        for target in order:
            path = self._shortest_path(current, (target.x, target.y), mission_map)
            total += self._path_length(path, start=current)
            planned.append(PlannedTarget(target=target, path_to_target=path))
            current = (target.x, target.y)
        return_path = self._shortest_path(current, home, mission_map)
        total += self._path_length(return_path, start=current)
        return MissionPlan(
            method=method,
            targets=tuple(planned),
            return_path=return_path,
            route_length_m=total,
            estimated_total_seconds=self._estimate_duration(total, len(planned)),
            skipped=tuple(skipped),
        )

    @staticmethod
    def _path_length(path: Sequence[Point], start: Point | None = None) -> float:
        if not path:
            return 0.0
        points = ([start] if start is not None else []) + list(path)
        return sum(distance(points[index - 1], points[index]) for index in range(1, len(points)))

    @lru_cache(maxsize=4096)
    def _shortest_path(self, start: Point, end: Point, mission_map: MissionMap) -> tuple[Point, ...]:
        polygons = tuple(zone.vertices for zone in mission_map.forbidden_zones)
        if segment_is_safe(start, end, polygons, self.clearance_m):
            return (end,)

        resolution = self.grid_resolution_m
        columns = int(round(mission_map.field_width / resolution)) + 1
        rows = int(round(mission_map.field_height / resolution)) + 1

        def point_for(node: tuple[int, int]) -> Point:
            return (node[0] * resolution, node[1] * resolution)

        def allowed(node: tuple[int, int]) -> bool:
            point = point_for(node)
            if not (0.0 <= point[0] <= mission_map.field_width and 0.0 <= point[1] <= mission_map.field_height):
                return False
            return all(clearance_to_polygon(point, polygon) >= self.clearance_m for polygon in polygons)

        def nearest_allowed(point: Point) -> tuple[int, int]:
            base = (
                max(0, min(columns - 1, round(point[0] / resolution))),
                max(0, min(rows - 1, round(point[1] / resolution))),
            )
            if allowed(base) and segment_is_safe(point, point_for(base), polygons, self.clearance_m):
                return base
            for radius in range(1, max(columns, rows)):
                candidates = []
                for dc in range(-radius, radius + 1):
                    candidates.extend(((base[0] + dc, base[1] - radius), (base[0] + dc, base[1] + radius)))
                for dr in range(-radius + 1, radius):
                    candidates.extend(((base[0] - radius, base[1] + dr), (base[0] + radius, base[1] + dr)))
                candidates = [node for node in candidates if 0 <= node[0] < columns and 0 <= node[1] < rows]
                candidates.sort(key=lambda node: distance(point, point_for(node)))
                for node in candidates:
                    if allowed(node) and segment_is_safe(point, point_for(node), polygons, self.clearance_m):
                        return node
            raise NoSafePathError("Точка недостижима")

        start_node = nearest_allowed(start)
        end_node = nearest_allowed(end)
        frontier: list[tuple[float, tuple[int, int]]] = [(0.0, start_node)]
        cost = {start_node: 0.0}
        parent: dict[tuple[int, int], tuple[int, int]] = {}
        moves = (
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1),
        )

        while frontier:
            _, current = heapq.heappop(frontier)
            if current == end_node:
                break
            for dc, dr in moves:
                neighbor = (current[0] + dc, current[1] + dr)
                if not (0 <= neighbor[0] < columns and 0 <= neighbor[1] < rows) or not allowed(neighbor):
                    continue
                if dc and dr:
                    if not allowed((current[0] + dc, current[1])) or not allowed((current[0], current[1] + dr)):
                        continue
                current_point = point_for(current)
                neighbor_point = point_for(neighbor)
                if not segment_is_safe(current_point, neighbor_point, polygons, self.clearance_m):
                    continue
                new_cost = cost[current] + distance(current_point, neighbor_point)
                if new_cost >= cost.get(neighbor, math.inf):
                    continue
                cost[neighbor] = new_cost
                parent[neighbor] = current
                priority = new_cost + distance(neighbor_point, point_for(end_node))
                heapq.heappush(frontier, (priority, neighbor))

        if end_node not in cost:
            raise NoSafePathError("Безопасный маршрут не найден")

        nodes = [end_node]
        while nodes[-1] != start_node:
            nodes.append(parent[nodes[-1]])
        nodes.reverse()
        raw = [point_for(node) for node in nodes]
        raw.append(end)

        smoothed: list[Point] = []
        current_point = start
        index = 0
        while index < len(raw):
            furthest = index
            for candidate in range(len(raw) - 1, index - 1, -1):
                if segment_is_safe(current_point, raw[candidate], polygons, self.clearance_m):
                    furthest = candidate
                    break
            smoothed.append(raw[furthest])
            current_point = raw[furthest]
            index = furthest + 1
        return tuple(smoothed)
