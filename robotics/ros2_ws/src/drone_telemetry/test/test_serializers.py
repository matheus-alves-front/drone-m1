from types import SimpleNamespace
import unittest

from drone_telemetry.serializers import build_envelope, serialize_mission_status, serialize_vehicle_state


class TestTelemetrySerializers(unittest.TestCase):
    def test_serialize_vehicle_state(self) -> None:
        msg = SimpleNamespace(
            connected=True,
            armed=False,
            landed=True,
            failsafe=False,
            preflight_checks_pass=True,
            position_valid=True,
            nav_state="MANUAL",
            altitude_m=1.2,
            relative_altitude_m=0.4,
            absolute_altitude_m=101.2,
            latitude_deg=-22.0,
            longitude_deg=-43.0,
        )

        payload = serialize_vehicle_state(msg)

        self.assertTrue(payload["connected"])
        self.assertEqual(payload["nav_state"], "MANUAL")
        self.assertAlmostEqual(payload["absolute_altitude_m"], 101.2)

    def test_build_envelope_uses_ros_stamp(self) -> None:
        stamp = SimpleNamespace(sec=10, nanosec=20)
        mission = SimpleNamespace(
            mission_id="patrol_basic",
            phase="hover",
            active=True,
            completed=False,
            aborted=False,
            failed=False,
            terminal=False,
            succeeded=False,
            detail="waiting",
            current_waypoint_index=0,
            total_waypoints=3,
            last_command="takeoff",
        )

        envelope = build_envelope(
            run_id="run-a",
            source="telemetry_bridge",
            kind="mission_status",
            topic="/drone/mission_status",
            stamp=stamp,
            payload=serialize_mission_status(mission),
        )

        self.assertEqual(envelope.stamp_ns, 10_000_000_020)
        self.assertEqual(envelope.payload["phase"], "hover")


if __name__ == "__main__":
    unittest.main()
