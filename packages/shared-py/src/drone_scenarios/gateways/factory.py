from __future__ import annotations

from .fake import FakeVehicleGateway
from .mavsdk_backend import MavsdkVehicleGateway


def create_gateway(backend: str):
    if backend == "mavsdk":
        return MavsdkVehicleGateway()
    if backend == "fake-success":
        return FakeVehicleGateway()
    raise ValueError(f"unsupported backend: {backend}")
