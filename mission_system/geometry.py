"""Геометрические проверки поля, целей и запретных зон."""

from __future__ import annotations

import math
from typing import Iterable


Point = tuple[float, float]


def distance(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def point_in_polygon(point: Point, vertices: Iterable[Point]) -> bool:
    polygon = tuple(vertices)
    if len(polygon) < 3:
        return False
    x, y = point
    inside = False
    previous = polygon[-1]
    for current in polygon:
        x1, y1 = previous
        x2, y2 = current
        if _point_on_segment(point, previous, current):
            return True
        intersects = ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-15) + x1
        )
        if intersects:
            inside = not inside
        previous = current
    return inside


def _point_on_segment(point: Point, start: Point, end: Point, tolerance: float = 1e-9) -> bool:
    cross = (point[1] - start[1]) * (end[0] - start[0]) - (
        point[0] - start[0]
    ) * (end[1] - start[1])
    if abs(cross) > tolerance:
        return False
    dot = (point[0] - start[0]) * (end[0] - start[0]) + (
        point[1] - start[1]
    ) * (end[1] - start[1])
    if dot < -tolerance:
        return False
    squared_length = (end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2
    return dot <= squared_length + tolerance


def distance_point_to_segment(point: Point, start: Point, end: Point) -> float:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    squared_length = dx * dx + dy * dy
    if squared_length == 0:
        return distance(point, start)
    ratio = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dy
    ) / squared_length
    ratio = max(0.0, min(1.0, ratio))
    projection = (start[0] + ratio * dx, start[1] + ratio * dy)
    return distance(point, projection)


def clearance_to_polygon(point: Point, vertices: Iterable[Point]) -> float:
    polygon = tuple(vertices)
    if point_in_polygon(point, polygon):
        return 0.0
    return min(
        distance_point_to_segment(point, polygon[index - 1], polygon[index])
        for index in range(len(polygon))
    )


def orientation(a: Point, b: Point, c: Point) -> int:
    value = (b[1] - a[1]) * (c[0] - b[0]) - (b[0] - a[0]) * (c[1] - b[1])
    if abs(value) < 1e-12:
        return 0
    return 1 if value > 0 else 2


def segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
    o1 = orientation(a1, a2, b1)
    o2 = orientation(a1, a2, b2)
    o3 = orientation(b1, b2, a1)
    o4 = orientation(b1, b2, a2)
    if o1 != o2 and o3 != o4:
        return True
    return any(
        (
            orient == 0
            and _point_on_segment(point, start, end)
        )
        for orient, point, start, end in (
            (o1, b1, a1, a2),
            (o2, b2, a1, a2),
            (o3, a1, b1, b2),
            (o4, a2, b1, b2),
        )
    )


def segment_is_safe(
    start: Point,
    end: Point,
    polygons: Iterable[Iterable[Point]],
    clearance: float,
    sample_step: float = 0.025,
) -> bool:
    length = distance(start, end)
    samples = max(1, math.ceil(length / sample_step))
    for index in range(samples + 1):
        ratio = index / samples
        point = (
            start[0] + (end[0] - start[0]) * ratio,
            start[1] + (end[1] - start[1]) * ratio,
        )
        for polygon in polygons:
            if clearance_to_polygon(point, polygon) < clearance - 1e-9:
                return False
    return True
