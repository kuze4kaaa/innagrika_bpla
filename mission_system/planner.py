"""Планирование безопасного маршрута с возвратом и резервом времени."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import heapq
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
    distance_table_points: tuple[str, ...] = ()
    distance_table_m: tuple[tuple[float, ...], ...] = ()
    nearest_route_length_m: float | None = None

    @property
    def target_ids(self) -> tuple[str, ...]:
        return tuple(item.target.target_id for item in self.targets)


class NoSafePathError(ValueError):
    pass


class _HeldKarp:
    def __init__(self, distances: Sequence[Sequence[float]]) -> None:
        self.distances = distances
        self.target_count = len(distances) - 1

        @lru_cache(maxsize=None)
        def best_to(mask: int, last: int) -> tuple[float, int]:
            remaining = mask ^ (1 << (last - 1))
            if not remaining:
                return distances[0][last], 0
            return min(
                (best_to(remaining, previous)[0] + distances[previous][last], previous)
                for previous in _HeldKarp.indices(remaining)
            )

        self.best_to = best_to

    @staticmethod
    def indices(mask: int) -> Iterable[int]:
        while mask:
            bit = mask & -mask
            yield bit.bit_length()
            mask ^= bit

    def best_tour(self, mask: int) -> tuple[float, int]:
        if not mask:
            return 0.0, 0
        return min((self.best_to(mask, last)[0] + self.distances[last][0], last) for last in self.indices(mask))

    def order(self, mask: int, last: int) -> tuple[int, ...]:
        backward = []
        while last:
            backward.append(last)
            _, previous = self.best_to(mask, last)
            mask ^= 1 << (last - 1)
            last = previous
        return tuple(reversed(backward))


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
        home_paths = []

        for target in targets:
            point = (target.x, target.y)
            if any(clearance_to_polygon(point, polygon) < self.clearance_m for polygon in polygons):
                unreachable.append((target.target_id, "цель попала в расширенную запретную зону"))
            elif not self._within_field(point, mission_map):
                unreachable.append((target.target_id, "цель вне границ поля с безопасным отступом"))
            else:
                try:
                    path = self._shortest_path(home, point, mission_map)
                except NoSafePathError:
                    unreachable.append((target.target_id, "нет безопасного пути с возвратом"))
                else:
                    reachable.append(target)
                    home_paths.append(path)

        if not reachable:
            return MissionPlan(
                method="нет допустимых целей",
                targets=(),
                return_path=(home,),
                route_length_m=0.0,
                estimated_total_seconds=self.takeoff_landing_seconds + self.reserve_seconds,
                skipped=tuple(unreachable),
                distance_table_points=("Home-2",),
                distance_table_m=((0.0,),),
            )

        if len(reachable) > 16:
            raise ValueError("Точный расчёт Хелда-Карпа ограничен 16 достижимыми целями")
        points = [home, *((target.x, target.y) for target in reachable)]
        paths, distances = self._distance_table(points, home_paths, mission_map)
        solver = _HeldKarp(distances)
        full_mask = (1 << len(reachable)) - 1
        mask = full_mask
        length, last = solver.best_tour(mask)
        method = "Хелд-Карп; сравнение с методом ближайшей цели выполнено"
        if self._estimate_duration(length, len(reachable)) > self.execution_limit_seconds:
            mask, length, last = self._best_feasible_subset(reachable, solver, full_mask)
            method = "Хелд-Карп; выполнимое подмножество по приоритету и числу целей"
        skipped = unreachable + [
            (target.target_id, "не помещается во время с возвратом и резервом")
            for bit, target in enumerate(reachable) if not mask & (1 << bit)
        ]
        order = solver.order(mask, last)
        legs = tuple(PlannedTarget(reachable[to - 1], paths[start][to]) for start, to in zip((0, *order), order))
        return MissionPlan(
            method=method,
            targets=legs,
            return_path=paths[order[-1]][0] if order else (home,),
            route_length_m=length,
            estimated_total_seconds=self._estimate_duration(length, len(order)),
            skipped=tuple(skipped),
            distance_table_points=("Home-2", *(target.target_id for target in reachable)),
            distance_table_m=tuple(map(tuple, distances)),
            nearest_route_length_m=self._nearest_neighbor_length(distances),
        )

    def _estimate_duration(self, route_length: float, target_count: int) -> float:
        return (
            route_length / self.planning_speed_mps
            + target_count * (self.stabilization_seconds + self.action_seconds)
            + self.takeoff_landing_seconds
            + self.reserve_seconds
        )

    @staticmethod
    def _nearest_neighbor_length(distances: Sequence[Sequence[float]]) -> float:
        remaining = set(range(1, len(distances)))
        current = 0
        length = 0.0
        while remaining:
            target = min(remaining, key=lambda index: (distances[current][index], index))
            length += distances[current][target]
            remaining.remove(target)
            current = target
        return length + distances[current][0]

    def _best_feasible_subset(
        self, targets: Sequence[Target], solver: _HeldKarp, full_mask: int
    ) -> tuple[int, float, int]:
        best = (0, 0.0, 0)
        best_score = (-1, -1, -math.inf)
        for mask in range(1, full_mask):
            count = mask.bit_count()
            length, last = solver.best_tour(mask)
            duration = self._estimate_duration(length, count)
            if duration > self.execution_limit_seconds:
                continue
            priority = sum(targets[index - 1].priority for index in solver.indices(mask))
            score = (priority, count, -duration)
            if score > best_score:
                best_score = score
                best = (mask, length, last)
        return best

    def _distance_table(
        self, points: Sequence[Point], home_paths: Sequence[tuple[Point, ...]], mission_map: MissionMap
    ) -> tuple[list[list[tuple[Point, ...]]], list[list[float]]]:
        size = len(points)
        paths: list[list[tuple[Point, ...]]] = [[() for _ in points] for _ in points]
        distances = [[0.0] * size for _ in points]
        for start in range(size):
            for end in range(start + 1, size):
                if start == 0:
                    path = home_paths[end - 1]
                else:
                    # Если сетка не соединяет две цели напрямую, остаётся проверенный путь через базу.
                    through_home = paths[start][0] + paths[0][end]
                    try:
                        path = self._shortest_path(points[start], points[end], mission_map)
                    except NoSafePathError:
                        path = through_home
                    else:
                        if self._path_length(through_home, points[start]) < self._path_length(path, points[start]):
                            path = through_home
                paths[start][end] = path
                paths[end][start] = (points[start], *path[:-1])[::-1]
                distances[start][end] = distances[end][start] = self._path_length(path, points[start])
        return paths, distances

    def _within_field(self, point: Point, mission_map: MissionMap) -> bool:
        x, y = point
        return (self.clearance_m <= x <= mission_map.field_width - self.clearance_m
                and self.clearance_m <= y <= mission_map.field_height - self.clearance_m)

    @staticmethod
    def _path_length(path: Sequence[Point], start: Point | None = None) -> float:
        if not path:
            return 0.0
        points = ([start] if start is not None else []) + list(path)
        return sum(distance(points[index - 1], points[index]) for index in range(1, len(points)))

    @lru_cache(maxsize=4096)
    def _shortest_path(self, start: Point, end: Point, mission_map: MissionMap) -> tuple[Point, ...]:
        if not self._within_field(start, mission_map) or not self._within_field(end, mission_map):
            raise NoSafePathError("Начало или конец перехода вне границ с безопасным отступом")
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
            if not self._within_field(point, mission_map):
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
