"""
Модуль расчета производственной экономической модели (Задание 1.1)
Олимпиада Иннагрика 2026, полуфинал, профиль «Агротех»
Разработка системы взаимодействия двух БПЛА (АТ11-2)
"""

import sys
from typing import Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class AgrotechEconomics:
    """
    Класс для расчета и сравнения экономических показателей:
    1. Сплошная обработка всей площади.
    2. Двухуровневая схема: «Разведка БПЛА-разведчиком + локальное исполнение БПЛА-исполнителем».
    """
    def __init__(
        self,
        total_area_ha: float = 120.0,
        blanket_cost_per_ha: float = 1800.0,
        recon_cost_per_ha: float = 250.0,
        local_cost_per_ha: float = 2200.0,
        prep_cost_fixed: float = 15000.0
    ):
        self.S_total = total_area_ha
        self.C_blanket = blanket_cost_per_ha
        self.C_recon = recon_cost_per_ha
        self.C_local = local_cost_per_ha
        self.C_prep = prep_cost_fixed

    def cost_blanket(self) -> float:
        """Затраты на сплошную обработку всей площади (руб)."""
        return self.S_total * self.C_blanket

    def cost_two_drone_system(self, target_fraction: float) -> Dict[str, float]:
        """
        Затраты на двухуровневую схему при заданной доле целевых участков p in [0, 1].
        """
        if not (0.0 <= target_fraction <= 1.0):
            raise ValueError("Доля целевых участков p должна находиться в диапазоне [0, 1]")
        
        target_area = self.S_total * target_fraction
        recon_cost = self.S_total * self.C_recon
        local_cost = target_area * self.C_local
        prep_cost = self.C_prep
        total_cost = recon_cost + local_cost + prep_cost

        return {
            "target_fraction": target_fraction,
            "target_area_ha": target_area,
            "recon_cost_rub": recon_cost,
            "local_cost_rub": local_cost,
            "prep_cost_rub": prep_cost,
            "total_cost_rub": total_cost
        }

    def calculate_savings(self, target_fraction: float) -> Dict[str, Any]:
        """
        Расчет абсолютной и относительной экономии при доле p.
        """
        blanket_total = self.cost_blanket()
        two_drone_res = self.cost_two_drone_system(target_fraction)
        two_drone_total = two_drone_res["total_cost_rub"]
        
        savings_rub = blanket_total - two_drone_total
        savings_percent = (savings_rub / blanket_total) * 100.0

        return {
            "blanket_cost_rub": blanket_total,
            "two_drone_cost_rub": two_drone_total,
            "savings_rub": savings_rub,
            "savings_percent": savings_percent,
            "breakdown": two_drone_res
        }

    def find_breakeven_fraction(self) -> float:
        """
        Нахождение критической доли целевых участков p*, при которой стоимости сравняются:
        Cost_blanket = Cost_two_drone(p*)
        S_total * C_blanket = S_total * C_recon + (p* * S_total * C_local) + C_prep
        p* = (S_total * (C_blanket - C_recon) - C_prep) / (S_total * C_local)
        """
        numerator = self.S_total * (self.C_blanket - self.C_recon) - self.C_prep
        denominator = self.S_total * self.C_local
        p_star = numerator / denominator
        return p_star

def run_economic_analysis() -> None:
    econ = AgrotechEconomics()

    print("=" * 70)
    print("ЭКОНОМИЧЕСКИЙ АНАЛИЗ ПРОИЗВОДСТВЕННОЙ МОДЕЛИ (ЗАДАНИЕ 1.1)")
    print("=" * 70)

    # 1. Сплошная обработка
    c_blanket = econ.cost_blanket()
    print(f"Общая площадь поля: {econ.S_total:.1f} га")
    print(f"Стоимость сплошной обработки: {c_blanket:,.2f} ₽ (1 800 ₽/га)")
    print("-" * 70)

    # 2. Анализ при 20%
    res_20 = econ.calculate_savings(0.20)
    print("Сценарий 1: Базовый случай — доля целевых участков 20%:")
    print(f"  - Обрабатываемая площадь: {res_20['breakdown']['target_area_ha']:.1f} га")
    print(f"  - Стоимость сплошной обработки: {res_20['blanket_cost_rub']:,.2f} ₽")
    print(f"  - Затраты разведки (120 га * 250 ₽): {res_20['breakdown']['recon_cost_rub']:,.2f} ₽")
    print(f"  - Затраты локальной операции (24 га * 2200 ₽): {res_20['breakdown']['local_cost_rub']:,.2f} ₽")
    print(f"  - Подготовка карт и верификация: {res_20['breakdown']['prep_cost_rub']:,.2f} ₽")
    print(f"  - Итого затраты двух БПЛА: {res_20['two_drone_cost_rub']:,.2f} ₽")
    print(f"  - АБСОЛЮТНАЯ ЭКОНОМИЯ: {res_20['savings_rub']:,.2f} ₽")
    print(f"  - ОТНОСИТЕЛЬНАЯ ЭКОНОМИЯ: {res_20['savings_percent']:.2f}%")
    print("-" * 70)

    # 3. Анализ при 50%
    res_50 = econ.calculate_savings(0.50)
    print("Сценарий 2: Доля целевых участков 50%:")
    print(f"  - Обрабатываемая площадь: {res_50['breakdown']['target_area_ha']:.1f} га")
    print(f"  - Итого затраты двух БПЛА: {res_50['two_drone_cost_rub']:,.2f} ₽")
    print(f"  - АБСОЛЮТНАЯ ЭКОНОМИЯ: {res_50['savings_rub']:,.2f} ₽")
    print(f"  - ОТНОСИТЕЛЬНАЯ ЭКОНОМИЯ: {res_50['savings_percent']:.2f}%")
    print("-" * 70)

    # 4. Критическая доля (точка безубыточности)
    p_star = econ.find_breakeven_fraction()
    area_star = econ.S_total * p_star
    c_star = econ.cost_two_drone_system(p_star)["total_cost_rub"]
    print("Критическая точка безубыточности (равенство затрат):")
    print(f"  - Критическая доля целевых участков p*: {p_star * 100:.2f}% ({p_star:.6f})")
    print(f"  - Соответствующая целевая площадь: {area_star:.2f} га")
    print(f"  - Затраты в точке безубыточности: {c_star:,.2f} ₽")
    print(f"  - Вывод: при p < {p_star*100:.2f}% выгоднее двухэтапная схема;")
    print(f"           при p > {p_star*100:.2f}% выгоднее сплошная обработка!")
    print("=" * 70)

if __name__ == "__main__":
    run_economic_analysis()
