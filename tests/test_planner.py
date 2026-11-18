import unittest

from mission_system.geometry import segment_is_safe
from mission_system.models import Target
from mission_system.planner import MissionPlanner
from tests.helpers import make_map


class PlannerTests(unittest.TestCase):
    def test_route_avoids_expanded_zones_and_returns_home(self):
        mission_map = make_map()
        planner = MissionPlanner()
        plan = planner.plan(mission_map)
        self.assertEqual(set(plan.target_ids), {"A1", "A2", "A3", "A4", "A5", "A6"})
        self.assertLessEqual(plan.estimated_total_seconds, 360.0)
        self.assertEqual(plan.return_path[-1], (0.4, 1.2))
        polygons = tuple(zone.vertices for zone in mission_map.forbidden_zones)
        current = (0.4, 1.2)
        for planned_target in plan.targets:
            for point in planned_target.path_to_target:
                self.assertTrue(segment_is_safe(current, point, polygons, 0.23))
                current = point
        for point in plan.return_path:
            self.assertTrue(segment_is_safe(current, point, polygons, 0.23))
            current = point

    def test_time_shortage_selects_safe_subset_and_explains_skips(self):
        mission_map = make_map()
        planner = MissionPlanner(execution_limit_seconds=125.0)
        plan = planner.plan(mission_map)
        self.assertLess(len(plan.targets), 6)
        self.assertLessEqual(plan.estimated_total_seconds, 125.0)
        self.assertTrue(plan.skipped)
        self.assertTrue(all(reason for _, reason in plan.skipped))

    def test_target_in_expanded_zone_is_skipped(self):
        targets = (Target("A1", "ACT-1", "A", 1.90, 2.0),)
        mission_map = make_map(targets=targets)
        plan = MissionPlanner().plan(mission_map)
        self.assertFalse(plan.targets)
        self.assertIn("расширенную запретную зону", plan.skipped[0][1])


if __name__ == "__main__":
    unittest.main()
