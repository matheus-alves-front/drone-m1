import asyncio
import unittest

from drone_mission.contracts import ConnectionContract, FlightContract, MissionContract, PatrolContract
from drone_mission.fake_gateway import FakeMissionGateway
from drone_mission.errors import MissionAbortRequested
from drone_mission.mission_executor import MissionExecutor
from drone_mission.mission_state_machine import MissionPhase, MissionStateMachine


def build_contract() -> MissionContract:
    return MissionContract(
        name="patrol_basic",
        scenario_path="simulation/scenarios/patrol_basic.json",
        objective="test patrol mission",
        connection=ConnectionContract(
            system_address="udp://:14540",
            connection_timeout_s=20.0,
            ready_timeout_s=20.0,
            action_timeout_s=20.0,
        ),
        flight=FlightContract(
            takeoff_altitude_m=3.0,
            hover_duration_s=0.0,
            arrival_tolerance_m=2.0,
            takeoff_timeout_s=20.0,
            waypoint_timeout_s=20.0,
            land_timeout_s=20.0,
            abort_land_timeout_s=20.0,
        ),
        patrol=PatrolContract(
            waypoint_offsets_north_m=[10.0, 10.0, 0.0],
            waypoint_offsets_east_m=[0.0, 10.0, 10.0],
            return_to_home=True,
        ),
    )


class TestMissionExecutor(unittest.TestCase):
    def test_executor_completes_patrol_flow(self) -> None:
        state_machine = MissionStateMachine("patrol_basic", total_waypoints=3)
        executor = MissionExecutor(FakeMissionGateway(), state_machine)

        asyncio.run(executor.run(build_contract(), should_abort=lambda: False))

        snapshot = state_machine.snapshot
        self.assertEqual(snapshot.phase, MissionPhase.COMPLETED)
        self.assertEqual(snapshot.current_waypoint_index, 3)

    def test_executor_aborts_with_fallback(self) -> None:
        state_machine = MissionStateMachine("patrol_basic", total_waypoints=3)
        executor = MissionExecutor(FakeMissionGateway(), state_machine)
        seen_patrol = {"value": False}

        def should_abort() -> bool:
            if state_machine.snapshot.phase == MissionPhase.PATROL and state_machine.snapshot.current_waypoint_index >= 1:
                seen_patrol["value"] = True
                return True
            return False

        asyncio.run(executor.run(build_contract(), should_abort=should_abort))

        snapshot = state_machine.snapshot
        self.assertTrue(seen_patrol["value"])
        self.assertEqual(snapshot.phase, MissionPhase.ABORTED)

    def test_executor_marks_failure_when_connection_breaks(self) -> None:
        state_machine = MissionStateMachine("patrol_basic", total_waypoints=3)
        executor = MissionExecutor(FakeMissionGateway(failure_mode="connection"), state_machine)

        try:
            asyncio.run(executor.run(build_contract(), should_abort=lambda: False))
        except Exception:
            pass

        self.assertEqual(state_machine.snapshot.phase, MissionPhase.FAILED)

    def test_executor_interrupts_long_waits_when_abort_is_requested(self) -> None:
        class SlowWaitGateway(FakeMissionGateway):
            async def wait_until_near(self, target, tolerance_m, timeout_s):
                del target, tolerance_m, timeout_s
                await asyncio.sleep(5.0)
                return self.position

        state_machine = MissionStateMachine("patrol_basic", total_waypoints=3)
        executor = MissionExecutor(SlowWaitGateway(), state_machine)
        abort_switch = {"armed": False}

        async def trigger_abort() -> None:
            while state_machine.snapshot.phase != MissionPhase.PATROL:
                await asyncio.sleep(0.01)
            abort_switch["armed"] = True

        async def run_case() -> None:
            trigger_task = asyncio.create_task(trigger_abort())
            await executor.run(build_contract(), should_abort=lambda: abort_switch["armed"])
            await trigger_task

        asyncio.run(run_case())

        self.assertEqual(state_machine.snapshot.phase, MissionPhase.ABORTED)

    def test_executor_waits_for_visual_lock_before_patrol(self) -> None:
        state_machine = MissionStateMachine("patrol_basic", total_waypoints=3)
        visual_lock_observed = {"value": False}

        async def wait_for_visual_lock(timeout_s: float) -> None:
            self.assertGreaterEqual(timeout_s, 5.0)
            visual_lock_observed["value"] = True
            await asyncio.sleep(0)

        executor = MissionExecutor(
            FakeMissionGateway(),
            state_machine,
            wait_for_visual_lock=wait_for_visual_lock,
            visual_lock_timeout_s=10.0,
        )

        asyncio.run(executor.run(build_contract(), should_abort=lambda: False))

        self.assertTrue(visual_lock_observed["value"])
        self.assertEqual(state_machine.snapshot.phase, MissionPhase.COMPLETED)


if __name__ == "__main__":
    unittest.main()
