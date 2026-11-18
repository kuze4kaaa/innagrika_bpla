"""
Расчет бюджета погрешностей и безопасных зон (Задания 1.3 и 1.4)
Олимпиада Иннагрика 2026, полуфинал, профиль «Агротех»
Разработка системы взаимодействия двух БПЛА (АТ11-2)
"""

import sys
from typing import Dict, Any
import math

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class ErrorBudgetCalculator:
    """
    Класс для расчета геометрических допусков, бюджета погрешностей и
    буферизации запретных зон в координатах учебного полигона F.
    """
    def __init__(
        self,
        e_target: float = 0.07,     # Ошибка положения цели по разведке, м
        e_exec: float = 0.06,       # Ошибка положения исполнителя, м
        e_align: float = 0.02,      # Ошибка взаимной привязки систем, м
        r_impact: float = 0.04,     # Условный радиус воздействия, м
        R_target: float = 0.25,     # Рабочая область цели, м
        R_drone: float = 0.10,      # Горизонтальный радиус БПЛА, м
        d_margin: float = 0.05      # Дополнительный запас, м
    ):
        self.e_target = e_target
        self.e_exec = e_exec
        self.e_align = e_align
        self.r_impact = r_impact
        self.R_target = R_target
        self.R_drone = R_drone
        self.d_margin = d_margin

    def calculate_operation_budget(self) -> Dict[str, Any]:
        """
        Проверка условия Задания 1.3:
        e_sum = e_target + e_exec + e_align (консервативная линейная сумма)
        Условие надежности: e_sum + r_возд <= R_цели
        Запас: Delta = R_цели - (e_sum + r_возд)
        """
        e_sum = self.e_target + self.e_exec + self.e_align
        total_coverage_radius = e_sum + self.r_impact
        is_safe = total_coverage_radius <= self.R_target
        remaining_margin = self.R_target - total_coverage_radius

        # Квадратичное сложение (RSS - Root Sum of Squares) для сравнения
        e_rss = math.sqrt(self.e_target**2 + self.e_exec**2 + self.e_align**2)
        total_rss = e_rss + self.r_impact
        margin_rss = self.R_target - total_rss

        return {
            "e_target_m": self.e_target,
            "e_exec_m": self.e_exec,
            "e_align_m": self.e_align,
            "e_sum_linear_m": e_sum,
            "e_rss_m": e_rss,
            "r_impact_m": self.r_impact,
            "R_target_m": self.R_target,
            "total_coverage_linear_m": total_coverage_radius,
            "total_coverage_rss_m": total_rss,
            "is_condition_met": is_safe,
            "remaining_margin_m": remaining_margin,
            "remaining_margin_rss_m": margin_rss
        }

    def calculate_safety_inflation(self) -> Dict[str, float]:
        """
        Расчет расширения запретных зон Задания 1.4:
        Расширение запретной зоны = R_drone + d_margin + e_exec + e_align
        """
        safety_expansion = self.R_drone + self.d_margin + self.e_exec + self.e_align
        return {
            "R_drone_m": self.R_drone,
            "d_margin_m": self.d_margin,
            "e_exec_m": self.e_exec,
            "e_align_m": self.e_align,
            "safety_expansion_m": safety_expansion
        }

def run_budget_analysis() -> None:
    calc = ErrorBudgetCalculator()
    op_res = calc.calculate_operation_budget()
    safe_res = calc.calculate_safety_inflation()

    print("=" * 70)
    print("БЮДЖЕТ ПОГРЕШНОСТЕЙ И БЕЗОПАСНАЯ ГЕОМЕТРИЯ (ЗАДАНИЯ 1.3 И 1.4)")
    print("=" * 70)
    print("1. Бюджет погрешностей рабочей операции:")
    print(f"  - Ошибка разведчика (e_target): {op_res['e_target_m']:.3f} м (7 см)")
    print(f"  - Ошибка исполнителя (e_exec): {op_res['e_exec_m']:.3f} м (6 см)")
    print(f"  - Ошибка взаимной привязки (e_align): {op_res['e_align_m']:.3f} м (2 см)")
    print(f"  - Консервативная сумма погрешностей (e_sum): {op_res['e_sum_linear_m']:.3f} м (15 см)")
    print(f"  - Условный радиус воздействия (r_возд): {op_res['r_impact_m']:.3f} м (4 см)")
    print(f"  - Максимальный вынос пятна воздействия (e_sum + r_возд): {op_res['total_coverage_linear_m']:.3f} м (19 см)")
    print(f"  - Радиус допустимой рабочей области (R_цели): {op_res['R_target_m']:.3f} м (25 см)")
    print(f"  - Проверка условия (e_sum + r_возд <= R_цели): {'ВЫПОЛНЕНО' if op_res['is_condition_met'] else 'НАРУШЕНО'}")
    print(f"  - ОСТАВШИЙСЯ ГЕОМЕТРИЧЕСКИЙ ЗАПАС: {op_res['remaining_margin_m']:.3f} м ({op_res['remaining_margin_m']*100:.1f} см)")
    print(f"  - (Справочно при квадратичном сложении RSS): e_rss = {op_res['e_rss_m']:.3f} м, запас = {op_res['remaining_margin_rss_m']:.3f} м")
    print("-" * 70)
    print("2. Расширение (буферизация) запретных зон:")
    print(f"  - Радиус БПЛА (R_drone): {safe_res['R_drone_m']:.3f} м (10 см)")
    print(f"  - Дополнительный запас (d_margin): {safe_res['d_margin_m']:.3f} м (5 см)")
    print(f"  - Ошибка исполнителя (e_exec): {safe_res['e_exec_m']:.3f} м (6 см)")
    print(f"  - Взаимная привязка (e_align): {safe_res['e_align_m']:.3f} м (2 см)")
    print(f"  - ИТОГОВОЕ РАСШИРЕНИЕ ЗАПРЕТНОЙ ЗОНЫ: {safe_res['safety_expansion_m']:.3f} м ({safe_res['safety_expansion_m']*100:.1f} см)")
    print("=" * 70)

if __name__ == "__main__":
    run_budget_analysis()
