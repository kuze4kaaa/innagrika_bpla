import math
import unittest

from mission_system.coordinates import Homography2D, RigidTransform2D
from mission_system.observations import Observation, fuse_observations


class CoordinateTests(unittest.TestCase):
    def test_homography_and_independent_check_points(self):
        image = ((0, 0), (100, 0), (100, 100), (0, 100))
        field = ((0, 0), (6, 0), (6, 4), (0, 4))
        transform = Homography2D.fit(image, field)
        self.assertAlmostEqual(transform.transform((50, 50))[0], 3.0, places=9)
        self.assertAlmostEqual(transform.transform((50, 50))[1], 2.0, places=9)
        mean_error, max_error = transform.errors(((25, 25), (75, 75)), ((1.5, 1.0), (4.5, 3.0)))
        self.assertLess(mean_error, 1e-9)
        self.assertLess(max_error, 1e-9)

    def test_each_drone_has_its_own_transform_to_f(self):
        recon = RigidTransform2D("RECON-CAL-1", math.pi / 2, 1.0, 2.0)
        executor = RigidTransform2D("EXEC-CAL-1", 0.0, 0.2, 0.4)
        self.assertNotEqual(recon.to_field((1.0, 0.0)), executor.to_field((1.0, 0.0)))
        point = (2.0, 3.0)
        local = recon.from_field(point)
        restored = recon.to_field(local)
        self.assertAlmostEqual(restored[0], point[0])
        self.assertAlmostEqual(restored[1], point[1])


class ObservationTests(unittest.TestCase):
    def test_repeated_observations_are_merged(self):
        result = fuse_observations(
            (
                Observation("O1", "F1", "A", 1.00, 1.00, 0.9),
                Observation("O2", "F2", "A", 1.04, 1.02, 0.8),
            )
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].object_class, "A")
        self.assertEqual(result[0].source_frame_ids, ("F1", "F2"))

    def test_conflicting_observations_become_u(self):
        result = fuse_observations(
            (
                Observation("O1", "F1", "A", 1.00, 1.00, 0.9),
                Observation("O2", "F2", "B", 1.04, 1.02, 0.9),
            )
        )
        self.assertEqual(result[0].object_class, "U")
        self.assertEqual(result[0].confidence_label, "uncertain")


if __name__ == "__main__":
    unittest.main()
