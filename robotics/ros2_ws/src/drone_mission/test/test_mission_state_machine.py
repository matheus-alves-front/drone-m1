import unittest

from drone_mission.mission_state_machine import MissionPhase, MissionStateMachine


class TestMissionStateMachine(unittest.TestCase):
    def test_state_machine_allows_patrol_flow(self) -> None:
        machine = MissionStateMachine("patrol_basic", total_waypoints=3)

        machine.transition(MissionPhase.WAITING_FOR_SYSTEM, detail="waiting")
        machine.transition(MissionPhase.ARMING, detail="arming")
        machine.transition(MissionPhase.TAKEOFF, detail="takeoff")
        machine.transition(MissionPhase.HOVER, detail="hover")
        machine.transition(MissionPhase.PATROL, detail="wp1", current_waypoint_index=1)
        machine.transition(MissionPhase.PATROL, detail="wp2", current_waypoint_index=2)
        machine.transition(MissionPhase.RETURN_TO_HOME, detail="rth", current_waypoint_index=3)
        machine.transition(MissionPhase.LANDING, detail="landing", current_waypoint_index=3)
        snapshot = machine.transition(MissionPhase.COMPLETED, detail="done", current_waypoint_index=3)

        self.assertTrue(snapshot.completed)
        self.assertFalse(snapshot.active)
        self.assertEqual(snapshot.current_waypoint_index, 3)

    def test_state_machine_rejects_invalid_transition(self) -> None:
        machine = MissionStateMachine("patrol_basic", total_waypoints=1)

        with self.assertRaises(ValueError):
            machine.transition(MissionPhase.PATROL, detail="invalid")

    def test_state_machine_abort_flow(self) -> None:
        machine = MissionStateMachine("patrol_basic", total_waypoints=2)
        machine.transition(MissionPhase.WAITING_FOR_SYSTEM, detail="waiting")
        machine.transition(MissionPhase.ARMING, detail="arming")
        machine.transition(MissionPhase.ABORTING, detail="abort")
        snapshot = machine.transition(MissionPhase.ABORTED, detail="aborted")

        self.assertTrue(snapshot.aborted)
        self.assertFalse(snapshot.failed)


if __name__ == "__main__":
    unittest.main()
