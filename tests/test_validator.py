from dataclasses import replace
from datetime import timedelta
import unittest

from mission_system.models import PolygonZone, Target
from mission_system.validator import MapValidator
from tests.helpers import BASE_TIME, make_map, replace_and_sign


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = MapValidator({"RECON-CAL-1"}, {"EXEC-CAL-1"})

    def test_valid_map(self):
        result = self.validator.validate(make_map(), now=BASE_TIME + timedelta(minutes=1))
        self.assertTrue(result.valid, result.errors)

    def test_centimetres_are_rejected_without_guessing(self):
        mission_map = replace_and_sign(make_map(), units="cm")
        result = self.validator.validate(mission_map, now=BASE_TIME)
        self.assertFalse(result.valid)
        self.assertTrue(any("автопересчёт запрещён" in error for error in result.errors))

    def test_unknown_calibration_is_rejected(self):
        mission_map = replace_and_sign(make_map(), calibration_id_executor="UNKNOWN")
        result = self.validator.validate(mission_map, now=BASE_TIME)
        self.assertFalse(result.valid)

    def test_expired_map_is_rejected(self):
        result = self.validator.validate(make_map(), now=BASE_TIME + timedelta(minutes=16))
        self.assertFalse(result.valid)
        self.assertIn("карта просрочена", result.errors)

    def test_map_is_expired_at_exact_expiration_time(self):
        result = self.validator.validate(make_map(), now=BASE_TIME + timedelta(minutes=15))
        self.assertFalse(result.valid)
        self.assertIn("карта просрочена", result.errors)

    def test_checksum_damage_is_rejected(self):
        mission_map = replace(make_map(), checksum="0" * 64)
        result = self.validator.validate(mission_map, now=BASE_TIME)
        self.assertFalse(result.valid)
        self.assertIn("контрольная сумма не совпадает", result.errors)

    def test_duplicate_action_is_rejected(self):
        targets = (
            Target("A1", "ACT-1", "A", 1.0, 1.0),
            Target("A2", "ACT-1", "A", 1.5, 1.0),
        )
        result = self.validator.validate(make_map(targets=targets), now=BASE_TIME)
        self.assertFalse(result.valid)
        self.assertTrue(any("дублируется action_id" in error for error in result.errors))

    def test_b_or_u_cannot_enter_task_map(self):
        targets = (Target("B1", "ACT-B", "B", 1.0, 1.0),)
        result = self.validator.validate(make_map(targets=targets), now=BASE_TIME)
        self.assertFalse(result.valid)
        self.assertTrue(any("не класса A" in error for error in result.errors))

    def test_target_in_forbidden_zone_is_rejected(self):
        targets = (Target("A1", "ACT-1", "A", 2.5, 2.0),)
        zones = (PolygonZone("NFZ", ((2.0, 1.5), (3.0, 1.5), (3.0, 2.5), (2.0, 2.5))),)
        result = self.validator.validate(make_map(targets=targets, zones=zones), now=BASE_TIME)
        self.assertFalse(result.valid)
        self.assertTrue(any("находится в запретной зоне" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
