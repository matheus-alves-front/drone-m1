import unittest

from drone_safety.contracts import SafetyConfig, SafetySignals
from drone_safety.rules import evaluate_safety, horizontal_distance_m


class TestSafetyRules(unittest.TestCase):
    def test_horizontal_distance_returns_zero_for_same_point(self) -> None:
        self.assertAlmostEqual(horizontal_distance_m(-22.0, -43.0, -22.0, -43.0), 0.0)

    def test_px4_failsafe_has_highest_priority(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=True,
                position_valid=True,
                home_position_valid=True,
                distance_from_home_m=100.0,
                relative_altitude_m=20.0,
                gps_lost=True,
            ),
        )

        self.assertEqual(decision.rule, "px4_failsafe_active")

    def test_geofence_breach_triggers_rtl(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(geofence_max_distance_m=10.0),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=False,
                position_valid=True,
                home_position_valid=True,
                distance_from_home_m=12.0,
                relative_altitude_m=3.0,
            ),
        )

        self.assertEqual(decision.rule, "geofence_breach")
        self.assertEqual(decision.action, "return_to_home")

    def test_gps_loss_triggers_land(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=False,
                position_valid=False,
                home_position_valid=False,
                gps_lost=True,
            ),
        )

        self.assertEqual(decision.rule, "gps_loss")
        self.assertEqual(decision.action, "land")

    def test_rc_loss_triggers_return_to_home(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=False,
                position_valid=True,
                home_position_valid=True,
                rc_lost=True,
            ),
        )

        self.assertEqual(decision.rule, "rc_loss")
        self.assertEqual(decision.action, "return_to_home")

    def test_data_link_loss_triggers_return_to_home(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=False,
                position_valid=True,
                home_position_valid=True,
                data_link_lost=True,
            ),
        )

        self.assertEqual(decision.rule, "data_link_loss")
        self.assertEqual(decision.action, "return_to_home")

    def test_perception_timeout_triggers_land(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(require_perception_heartbeat=True),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=False,
                position_valid=True,
                home_position_valid=True,
                perception_timeout=True,
            ),
        )

        self.assertEqual(decision.rule, "perception_timeout")
        self.assertEqual(decision.action, "land")

    def test_perception_latency_triggers_land(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(require_perception_heartbeat=True),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=True,
                vehicle_landed=False,
                vehicle_failsafe=False,
                position_valid=True,
                home_position_valid=True,
                perception_latency_exceeded=True,
            ),
        )

        self.assertEqual(decision.rule, "perception_latency")
        self.assertEqual(decision.action, "land")

    def test_idle_vehicle_does_not_trigger_fault_actions(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(),
            SafetySignals(
                mission_active=False,
                vehicle_connected=True,
                vehicle_armed=False,
                vehicle_landed=True,
                vehicle_failsafe=False,
                position_valid=True,
                home_position_valid=True,
                rc_lost=True,
            ),
        )

        self.assertIsNone(decision)

    def test_mission_bootstrap_on_ground_does_not_trigger_safety_before_flight(self) -> None:
        decision = evaluate_safety(
            SafetyConfig(),
            SafetySignals(
                mission_active=True,
                vehicle_connected=True,
                vehicle_armed=False,
                vehicle_landed=True,
                vehicle_failsafe=True,
                position_valid=True,
                home_position_valid=True,
                distance_from_home_m=100.0,
                relative_altitude_m=20.0,
                rc_lost=True,
                gps_lost=True,
            ),
        )

        self.assertIsNone(decision)
