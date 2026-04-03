import unittest

from drone_perception.detection import DetectionSample
from drone_perception.tracking import SingleObjectTracker


class TestTracker(unittest.TestCase):
    def test_tracker_acquires_and_updates_target(self) -> None:
        tracker = SingleObjectTracker(reacquire_distance_px=48.0)
        acquired = tracker.update(
            DetectionSample(detected=True, label="sim_target", confidence=0.9, center_x=10.0, center_y=20.0, width=30.0, height=30.0, area_ratio=0.1),
        )
        self.assertTrue(acquired.tracked)
        self.assertEqual(acquired.state, "locked")
        tracked = tracker.update(
            DetectionSample(detected=True, label="sim_target", confidence=0.8, center_x=12.0, center_y=22.0, width=31.0, height=31.0, area_ratio=0.1),
        )
        self.assertTrue(tracked.tracked)
        self.assertEqual(tracked.state, "tracking")
        self.assertEqual(tracked.track_id, acquired.track_id)

    def test_tracker_marks_target_lost_after_missing_detection(self) -> None:
        tracker = SingleObjectTracker(reacquire_distance_px=48.0)
        tracker.update(
            DetectionSample(detected=True, label="sim_target", confidence=0.9, center_x=10.0, center_y=20.0, width=30.0, height=30.0, area_ratio=0.1),
        )
        lost = tracker.update(
            DetectionSample(detected=False, label="sim_target", confidence=0.0, center_x=0.0, center_y=0.0, width=0.0, height=0.0, area_ratio=0.0),
        )
        self.assertFalse(lost.tracked)
        self.assertEqual(lost.state, "lost")
