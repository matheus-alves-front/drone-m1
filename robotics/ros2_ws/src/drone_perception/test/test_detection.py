import unittest

import numpy as np

from drone_perception.detection import detect_primary_target


class TestDetection(unittest.TestCase):
    def test_detect_primary_target_finds_red_blob(self) -> None:
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        frame[80:160, 110:210] = (0, 0, 255)

        detection = detect_primary_target(frame)

        self.assertTrue(detection.detected)
        self.assertGreater(detection.confidence, 0.5)
        self.assertGreater(detection.area_ratio, 0.01)
        self.assertAlmostEqual(detection.center_x, 160.0, delta=8.0)
        self.assertAlmostEqual(detection.center_y, 120.0, delta=8.0)

    def test_detect_primary_target_returns_false_without_target_blob(self) -> None:
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        frame[:, :] = (255, 0, 0)

        detection = detect_primary_target(frame)

        self.assertFalse(detection.detected)


if __name__ == "__main__":
    unittest.main()
