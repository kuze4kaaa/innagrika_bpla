import unittest

from analytics.economics_calculator import AgrotechEconomics
from analytics.error_budget import ErrorBudgetCalculator


class EconomicsTests(unittest.TestCase):
    def test_case_values(self):
        calculator = AgrotechEconomics()
        self.assertEqual(calculator.cost_blanket(), 216000.0)
        result_20 = calculator.calculate_savings(0.20)
        self.assertEqual(result_20["two_drone_cost_rub"], 97800.0)
        self.assertEqual(result_20["savings_rub"], 118200.0)
        result_50 = calculator.calculate_savings(0.50)
        self.assertEqual(result_50["two_drone_cost_rub"], 177000.0)
        self.assertEqual(result_50["savings_rub"], 39000.0)
        self.assertAlmostEqual(calculator.find_breakeven_fraction(), 0.6477272727)

    def test_invalid_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            AgrotechEconomics(total_area_ha=0)
        with self.assertRaises(ValueError):
            AgrotechEconomics(local_cost_per_ha=-1)
        with self.assertRaises(ValueError):
            AgrotechEconomics().cost_two_drone_system(1.01)


class ErrorBudgetTests(unittest.TestCase):
    def test_case_values(self):
        calculator = ErrorBudgetCalculator()
        operation = calculator.calculate_operation_budget()
        safety = calculator.calculate_safety_inflation()
        self.assertAlmostEqual(operation["e_sum_linear_m"], 0.15)
        self.assertAlmostEqual(operation["total_coverage_linear_m"], 0.19)
        self.assertAlmostEqual(operation["remaining_margin_m"], 0.06)
        self.assertTrue(operation["is_condition_met"])
        self.assertAlmostEqual(safety["safety_expansion_m"], 0.23)

    def test_negative_error_is_rejected(self):
        with self.assertRaises(ValueError):
            ErrorBudgetCalculator(e_target=-0.01)


if __name__ == "__main__":
    unittest.main()
