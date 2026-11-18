from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from mission_system.executor import ActionRegistry, Executor, ExecutorState, Pose
from mission_system.validator import MapValidator, ValidationError
from tests.helpers import BASE_TIME, make_map


def pose_at(time, x=1.0, y=0.8, z=1.2, speed=0.0, error=0.04):
    return Pose(x=x, y=y, z=z, speed_mps=speed, error_m=error, measured_at=time)


def advance(executor, start, seconds, step=0.1):
    count = int(round(seconds / step))
    state = executor.state
    for index in range(1, count + 1):
        current = start + timedelta(seconds=index * step)
        state = executor.update(pose_at(current), current)
    return state, start + timedelta(seconds=seconds)


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.validator = MapValidator({"RECON-CAL-1"}, {"EXEC-CAL-1"})

    def test_continuous_one_second_stabilization_and_two_second_operation(self):
        executor = Executor(self.validator, ActionRegistry())
        executor.load_map(make_map(), BASE_TIME)
        executor.select_target("A1", BASE_TIME)
        self.assertEqual(executor.update(pose_at(BASE_TIME), BASE_TIME), ExecutorState.STABILIZING)
        state, t1 = advance(executor, BASE_TIME, 1.0)
        self.assertEqual(state, ExecutorState.OPERATING)
        self.assertTrue(executor.led_enabled)
        state, _ = advance(executor, t1, 2.0)
        self.assertEqual(state, ExecutorState.CONFIRMED)
        self.assertFalse(executor.led_enabled)
        self.assertEqual(executor.registry.status("ACT-1"), "COMPLETED")

    def test_stale_pose_never_turns_led_on(self):
        executor = Executor(self.validator, ActionRegistry())
        executor.load_map(make_map(), BASE_TIME)
        executor.select_target("A1", BASE_TIME)
        now = BASE_TIME + timedelta(seconds=1)
        state = executor.update(pose_at(BASE_TIME), now)
        self.assertEqual(state, ExecutorState.NAVIGATING)
        self.assertFalse(executor.led_enabled)

    def test_excessive_position_error_never_turns_led_on(self):
        executor = Executor(self.validator, ActionRegistry())
        executor.load_map(make_map(), BASE_TIME)
        executor.select_target("A1", BASE_TIME)
        now = BASE_TIME + timedelta(seconds=1)
        state = executor.update(pose_at(now, error=0.061), now)
        self.assertEqual(state, ExecutorState.NAVIGATING)
        self.assertFalse(executor.led_enabled)

    def test_loss_of_localization_stops_led_and_marks_uncertain(self):
        executor = Executor(self.validator, ActionRegistry())
        executor.load_map(make_map(), BASE_TIME)
        executor.select_target("A1", BASE_TIME)
        executor.update(pose_at(BASE_TIME), BASE_TIME)
        _, t1 = advance(executor, BASE_TIME, 1.0)
        self.assertTrue(executor.led_enabled)
        executor.lose_localization(t1 + timedelta(milliseconds=100))
        self.assertFalse(executor.led_enabled)
        self.assertEqual(executor.state, ExecutorState.SAFE_STOP)
        self.assertEqual(executor.registry.status("ACT-1"), "UNCERTAIN")

    def test_gap_in_continuous_checks_stops_operation(self):
        executor = Executor(self.validator, ActionRegistry())
        executor.load_map(make_map(), BASE_TIME)
        executor.select_target("A1", BASE_TIME)
        executor.update(pose_at(BASE_TIME), BASE_TIME)
        _, t1 = advance(executor, BASE_TIME, 1.0)
        late = t1 + timedelta(seconds=0.31)
        state = executor.update(pose_at(late), late)
        self.assertEqual(state, ExecutorState.SAFE_STOP)
        self.assertFalse(executor.led_enabled)
        self.assertEqual(executor.registry.status("ACT-1"), "UNCERTAIN")

    def test_duplicate_is_blocked_after_restart(self):
        with TemporaryDirectory() as directory:
            registry_path = Path(directory) / "actions.json"
            first = Executor(self.validator, ActionRegistry(registry_path))
            first.load_map(make_map(), BASE_TIME)
            first.select_target("A1", BASE_TIME)
            first.update(pose_at(BASE_TIME), BASE_TIME)
            _, t1 = advance(first, BASE_TIME, 1.0)
            first.lose_control_link(t1 + timedelta(milliseconds=100))

            restarted = Executor(self.validator, ActionRegistry(registry_path))
            restarted.load_map(make_map(), t1)
            with self.assertRaises(ValueError):
                restarted.select_target("A1", t1)

    def test_map_expiry_during_operation_stops_new_action(self):
        executor = Executor(self.validator, ActionRegistry())
        mission_map = make_map(expires_delta=timedelta(seconds=2))
        executor.load_map(mission_map, BASE_TIME)
        executor.select_target("A1", BASE_TIME)
        executor.update(pose_at(BASE_TIME), BASE_TIME)
        _, t1 = advance(executor, BASE_TIME, 1.0)
        expired = BASE_TIME + timedelta(seconds=3)
        state = executor.update(pose_at(expired), expired)
        self.assertEqual(state, ExecutorState.SAFE_STOP)
        self.assertFalse(executor.led_enabled)
        self.assertEqual(executor.registry.status("ACT-1"), "UNCERTAIN")


if __name__ == "__main__":
    unittest.main()
