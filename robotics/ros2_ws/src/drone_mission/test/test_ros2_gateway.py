import asyncio
from dataclasses import dataclass
import unittest

from drone_mission.gateway import Ros2MissionGateway


@dataclass
class FakeVehicleState:
    connected: bool = True
    armed: bool = False
    landed: bool = True
    failsafe: bool = False
    preflight_checks_pass: bool = True
    position_valid: bool = True
    latitude_deg: float = -22.0
    longitude_deg: float = -43.0
    absolute_altitude_m: float = 100.0
    relative_altitude_m: float = 0.0


@dataclass
class FakeCommandStatus:
    command: str
    accepted: bool
    result_label: str


@dataclass
class SharedGatewayState:
    vehicle_state: FakeVehicleState | None = None
    command_status: FakeCommandStatus | None = None
    command_status_serial: int = 0


def build_gateway(shared: SharedGatewayState, published: list[tuple[str, dict[str, float]]]) -> Ros2MissionGateway:
    def publish_command(command: str, **payload: float) -> None:
        published.append((command, payload))

    def get_vehicle_state() -> FakeVehicleState | None:
        return shared.vehicle_state

    def get_command_status() -> tuple[int, FakeCommandStatus | None]:
        return shared.command_status_serial, shared.command_status

    return Ros2MissionGateway(
        publish_command=publish_command,
        get_vehicle_state=get_vehicle_state,
        get_command_status=get_command_status,
    )


class TestRos2MissionGateway(unittest.TestCase):
    def test_ros2_gateway_connect_waits_for_connected_state(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(vehicle_state=FakeVehicleState(connected=False, position_valid=False))
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)

            async def mark_connected() -> None:
                await asyncio.sleep(0.05)
                shared.vehicle_state = FakeVehicleState(connected=True, position_valid=True)

            ready_task = asyncio.create_task(mark_connected())
            await gateway.connect(system_address="unused", timeout_s=1.0)
            await ready_task

            self.assertEqual(published, [])

        asyncio.run(run_case())

    def test_ros2_gateway_waits_for_ready_position(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(
                vehicle_state=FakeVehicleState(
                    connected=True,
                    position_valid=True,
                    preflight_checks_pass=False,
                )
            )
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)

            position = await gateway.wait_until_ready_position(timeout_s=0.2)

            self.assertAlmostEqual(position.latitude_deg, -22.0)
            self.assertAlmostEqual(position.longitude_deg, -43.0)
            self.assertEqual(published, [])

        asyncio.run(run_case())

    def test_ros2_gateway_publishes_arm_and_waits_for_ack(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(vehicle_state=FakeVehicleState())
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)

            async def publish_ack() -> None:
                await asyncio.sleep(0.05)
                shared.command_status = FakeCommandStatus(command="arm", accepted=True, result_label="ACCEPTED")
                shared.command_status_serial += 1

            ack_task = asyncio.create_task(publish_ack())
            await gateway.arm(timeout_s=1.0)
            await ack_task

            self.assertEqual(published, [("arm", {})])
            self.assertEqual(gateway.last_command_name, "arm")

        asyncio.run(run_case())

    def test_ros2_gateway_wait_until_armed_requires_real_vehicle_state(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(
                vehicle_state=FakeVehicleState(
                    connected=True,
                    armed=False,
                    landed=True,
                ),
                command_status=FakeCommandStatus(command="arm", accepted=True, result_label="ACCEPTED"),
                command_status_serial=1,
            )
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)

            async def publish_armed_state() -> None:
                await asyncio.sleep(0.05)
                shared.vehicle_state = FakeVehicleState(
                    connected=True,
                    armed=True,
                    landed=False,
                )

            armed_task = asyncio.create_task(publish_armed_state())
            await gateway.wait_until_armed(timeout_s=1.0)
            await armed_task

            self.assertEqual(published, [])

        asyncio.run(run_case())

    def test_ros2_gateway_wait_until_armed_times_out_when_only_ack_arrives(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(
                vehicle_state=FakeVehicleState(
                    connected=True,
                    armed=False,
                    landed=True,
                ),
                command_status=FakeCommandStatus(command="arm", accepted=True, result_label="ACCEPTED"),
                command_status_serial=1,
            )
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)

            with self.assertRaisesRegex(Exception, "timed out while waiting for armed state"):
                await gateway.wait_until_armed(timeout_s=0.2)

            self.assertEqual(published, [])

        asyncio.run(run_case())

    def test_ros2_gateway_accepts_takeoff_altitude_even_if_landed_flag_lags(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(
                vehicle_state=FakeVehicleState(
                    connected=True,
                    position_valid=True,
                    landed=True,
                    relative_altitude_m=3.2,
                    absolute_altitude_m=103.2,
                )
            )
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)

            position = await gateway.wait_until_altitude(minimum_relative_altitude_m=3.0, timeout_s=0.2)

            self.assertAlmostEqual(position.relative_altitude_m, 3.2)
            self.assertEqual(published, [])

        asyncio.run(run_case())

    def test_ros2_gateway_applies_takeoff_altitude_tolerance(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(
                vehicle_state=FakeVehicleState(
                    connected=True,
                    position_valid=True,
                    landed=False,
                    relative_altitude_m=2.75,
                    absolute_altitude_m=102.75,
                )
            )
            published: list[tuple[str, dict[str, float]]] = []
            gateway = Ros2MissionGateway(
                publish_command=lambda command, **payload: published.append((command, payload)),
                get_vehicle_state=lambda: shared.vehicle_state,
                get_command_status=lambda: (shared.command_status_serial, shared.command_status),
                takeoff_altitude_tolerance_m=0.3,
            )

            position = await gateway.wait_until_altitude(minimum_relative_altitude_m=3.0, timeout_s=0.2)

            self.assertAlmostEqual(position.relative_altitude_m, 2.75)
            self.assertEqual(published, [])

        asyncio.run(run_case())

    def test_ros2_gateway_retries_temporarily_rejected_command(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(vehicle_state=FakeVehicleState())
            published: list[tuple[str, dict[str, float]]] = []
            attempt_counter = 0
            loop = asyncio.get_running_loop()

            def publish_command(command: str, **payload: float) -> None:
                nonlocal attempt_counter
                published.append((command, payload))
                attempt_counter += 1

                async def publish_status() -> None:
                    await asyncio.sleep(0.02)
                    if attempt_counter == 1:
                        shared.command_status = FakeCommandStatus(
                            command="arm",
                            accepted=False,
                            result_label="TEMPORARILY_REJECTED",
                        )
                    else:
                        shared.command_status = FakeCommandStatus(
                            command="arm",
                            accepted=True,
                            result_label="ACCEPTED",
                        )
                    shared.command_status_serial += 1

                loop.create_task(publish_status())

            gateway = Ros2MissionGateway(
                publish_command=publish_command,
                get_vehicle_state=lambda: shared.vehicle_state,
                get_command_status=lambda: (shared.command_status_serial, shared.command_status),
                command_retry_interval_s=0.1,
                max_command_retries=3,
            )
            await gateway.arm(timeout_s=1.0)

            self.assertEqual([command for command, _payload in published], ["arm", "arm"])

        asyncio.run(run_case())

    def test_ros2_gateway_publishes_goto_without_waiting_for_ack(self) -> None:
        async def run_case() -> None:
            shared = SharedGatewayState(vehicle_state=FakeVehicleState())
            published: list[tuple[str, dict[str, float]]] = []
            gateway = build_gateway(shared, published)
            await gateway.goto_location(
                latitude_deg=-22.1,
                longitude_deg=-43.1,
                absolute_altitude_m=103.0,
                yaw_deg=0.0,
                timeout_s=1.0,
            )

            self.assertEqual(
                published,
                [
                    (
                        "goto",
                        {
                            "target_latitude_deg": -22.1,
                            "target_longitude_deg": -43.1,
                            "target_absolute_altitude_m": 103.0,
                            "target_yaw_deg": 0.0,
                        },
                    )
                ],
            )
            self.assertEqual(gateway.last_command_name, "goto")

        asyncio.run(run_case())


if __name__ == "__main__":
    unittest.main()
