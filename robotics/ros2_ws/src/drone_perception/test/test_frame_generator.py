import unittest

from drone_perception.contracts import CameraConfig
from drone_perception.frame_generator import generate_frame, in_blackout_window


class TestFrameGenerator(unittest.TestCase):
    def test_generator_returns_expected_shape(self) -> None:
        config = CameraConfig(frame_width=320, frame_height=180)
        frame = generate_frame(config, elapsed_s=0.0)
        self.assertEqual(frame.shape, (180, 320, 3))

    def test_blackout_window_activates_in_configured_interval(self) -> None:
        config = CameraConfig(blackout_after_s=5.0, blackout_duration_s=2.0)
        self.assertFalse(in_blackout_window(config, 4.9))
        self.assertTrue(in_blackout_window(config, 5.5))
        self.assertFalse(in_blackout_window(config, 7.1))
