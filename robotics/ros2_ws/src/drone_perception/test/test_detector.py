import unittest

from drone_perception.detection import detect_primary_target
from drone_perception.frame_generator import generate_frame
from drone_perception.contracts import CameraConfig


class TestDetector(unittest.TestCase):
    def test_detector_finds_synthetic_target(self) -> None:
        frame = generate_frame(CameraConfig(), elapsed_s=0.0)
        result = detect_primary_target(frame)
        self.assertTrue(result.detected)
        self.assertEqual(result.label, "sim_target")
        self.assertGreater(result.confidence, 0.0)
        self.assertGreater(result.area_ratio, 0.0)
