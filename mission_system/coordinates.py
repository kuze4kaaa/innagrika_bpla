"""Координатная привязка изображения и локальных систем БПЛА к полю F."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence


Point = tuple[float, float]


def _solve_linear_system(matrix: list[list[float]], vector: list[float]) -> list[float]:
    n = len(vector)
    augmented = [row[:] + [vector[index]] for index, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) < 1e-12:
            raise ValueError("Опорные точки не задают однозначное преобразование")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        divisor = augmented[col][col]
        augmented[col] = [value / divisor for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [
                current - factor * reference
                for current, reference in zip(augmented[row], augmented[col])
            ]
    return [augmented[row][-1] for row in range(n)]


@dataclass(frozen=True)
class Homography2D:
    coefficients: tuple[float, float, float, float, float, float, float, float]

    @classmethod
    def fit(cls, image_points: Sequence[Point], field_points: Sequence[Point]) -> "Homography2D":
        if len(image_points) != len(field_points) or len(image_points) < 4:
            raise ValueError("Нужно не менее четырёх пар опорных точек")

        rows: list[list[float]] = []
        values: list[float] = []
        for (u, v), (x, y) in zip(image_points, field_points):
            rows.append([u, v, 1.0, 0.0, 0.0, 0.0, -u * x, -v * x])
            values.append(x)
            rows.append([0.0, 0.0, 0.0, u, v, 1.0, -u * y, -v * y])
            values.append(y)

        if len(rows) == 8:
            solution = _solve_linear_system(rows, values)
        else:
            normal = [[0.0] * 8 for _ in range(8)]
            rhs = [0.0] * 8
            for row, value in zip(rows, values):
                for i in range(8):
                    rhs[i] += row[i] * value
                    for j in range(8):
                        normal[i][j] += row[i] * row[j]
            solution = _solve_linear_system(normal, rhs)
        return cls(tuple(solution))

    def transform(self, point: Point) -> Point:
        u, v = point
        h11, h12, h13, h21, h22, h23, h31, h32 = self.coefficients
        denominator = h31 * u + h32 * v + 1.0
        if abs(denominator) < 1e-12:
            raise ValueError("Точка не может быть переведена в систему F")
        return (
            (h11 * u + h12 * v + h13) / denominator,
            (h21 * u + h22 * v + h23) / denominator,
        )

    def errors(self, image_points: Iterable[Point], field_points: Iterable[Point]) -> tuple[float, float]:
        errors = [
            math.hypot(predicted[0] - actual[0], predicted[1] - actual[1])
            for image, actual in zip(image_points, field_points)
            for predicted in [self.transform(image)]
        ]
        if not errors:
            raise ValueError("Нет проверочных точек")
        return sum(errors) / len(errors), max(errors)


@dataclass(frozen=True)
class RigidTransform2D:
    """Переход из локальной системы конкретного БПЛА в F."""

    calibration_id: str
    angle_rad: float
    offset_x: float
    offset_y: float

    def to_field(self, point: Point) -> Point:
        x_local, y_local = point
        cosine = math.cos(self.angle_rad)
        sine = math.sin(self.angle_rad)
        return (
            cosine * x_local - sine * y_local + self.offset_x,
            sine * x_local + cosine * y_local + self.offset_y,
        )

    def from_field(self, point: Point) -> Point:
        x_shifted = point[0] - self.offset_x
        y_shifted = point[1] - self.offset_y
        cosine = math.cos(self.angle_rad)
        sine = math.sin(self.angle_rad)
        return (
            cosine * x_shifted + sine * y_shifted,
            -sine * x_shifted + cosine * y_shifted,
        )
