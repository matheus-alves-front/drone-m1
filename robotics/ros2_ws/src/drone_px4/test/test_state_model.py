import unittest

from drone_px4.state_model import (
    geodetic_offset_m,
    local_position_from_reference,
    nav_state_name,
    normalize_command,
    resolve_takeoff_altitude,
)


class TestStateModel(unittest.TestCase):
    def test_nav_state_name_maps_known_values(self) -> None:
        self.assertEqual(nav_state_name(14), "OFFBOARD")
        self.assertEqual(nav_state_name(18), "AUTO_LAND")

    def test_nav_state_name_preserves_unknown_values(self) -> None:
        self.assertEqual(nav_state_name(255), "UNKNOWN_255")

    def test_normalize_command_handles_spaces_and_case(self) -> None:
        self.assertEqual(normalize_command(" TakeOff "), "takeoff")
        self.assertEqual(normalize_command("return to home"), "return_to_home")

    def test_resolve_takeoff_altitude_uses_requested_positive_value(self) -> None:
        self.assertEqual(resolve_takeoff_altitude(4.0, 3.0), 4.0)

    def test_resolve_takeoff_altitude_falls_back_to_default(self) -> None:
        self.assertEqual(resolve_takeoff_altitude(0.0, 3.0), 3.0)
        self.assertEqual(resolve_takeoff_altitude(-2.0, 0.1), 0.5)

    def test_geodetic_offset_m_returns_zero_for_same_position(self) -> None:
        north_m, east_m = geodetic_offset_m(-22.0, -43.0, -22.0, -43.0)
        self.assertAlmostEqual(north_m, 0.0)
        self.assertAlmostEqual(east_m, 0.0)

    def test_local_position_from_reference_preserves_reference_origin(self) -> None:
        north_m, east_m, down_m = local_position_from_reference(
            ref_lat_deg=-22.0,
            ref_lon_deg=-43.0,
            ref_alt_m=100.0,
            target_lat_deg=-22.0,
            target_lon_deg=-43.0,
            target_alt_m=100.0,
        )
        self.assertAlmostEqual(north_m, 0.0)
        self.assertAlmostEqual(east_m, 0.0)
        self.assertAlmostEqual(down_m, 0.0)


if __name__ == "__main__":
    unittest.main()
