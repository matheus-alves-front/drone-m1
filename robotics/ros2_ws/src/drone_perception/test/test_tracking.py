import unittest

from drone_perception.detection import DetectionSample
from drone_perception.tracking import SingleObjectTracker


class TestTracking(unittest.TestCase):
    def test_tracker_keeps_same_track_for_nearby_detection(self) -> None:
        tracker = SingleObjectTracker(reacquire_distance_px=30.0)

        first = tracker.update(
            DetectionSample(True, "sim_target", 0.9, 100.0, 100.0, 40.0, 40.0, 0.1)
        )
        second = tracker.update(
            DetectionSample(True, "sim_target", 0.8, 108.0, 104.0, 38.0, 38.0, 0.09)
        )

        self.assertTrue(first.tracked)
        self.assertTrue(second.tracked)
        self.assertEqual(first.track_id, second.track_id)
        self.assertEqual(second.state, "tracking")

    def test_tracker_marks_lost_when_detection_disappears(self) -> None:
        tracker = SingleObjectTracker()
        tracker.update(DetectionSample(True, "sim_target", 0.9, 100.0, 100.0, 40.0, 40.0, 0.1))

        lost = tracker.update(DetectionSample(False, "sim_target", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0))

        self.assertFalse(lost.tracked)
        self.assertEqual(lost.state, "lost")


if __name__ == "__main__":
    unittest.main()
