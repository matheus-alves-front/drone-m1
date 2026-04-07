# Mark 1 Software Architecture

## Arquitetura-alvo

```text
Operator UI
    |
    v
Control API / Control Plane
    |-----------------------------|
    |             |               |
    v             v               v
Runtime Orchestrator   Action/Scenario Service   Read Model Query Layer
    |             |               |
    v             v               v
Adapters: shell / ROS 2 / MAVSDK / Telemetry API / Dashboard websocket
    |
    v
PX4 + Gazebo + XRCE + ROS 2 graph
```

## Bounded Contexts

### 1. Control Plane
Responsável por:
- actions
- sessions
- runs
- orchestration
- capability discovery
- session lifecycle
- scenario lifecycle

### 2. Runtime Adapters
Responsável por:
- start/stop sim
- ROS 2 command publishing
- MAVSDK scenario execution
- future hardware adapters

### 3. Mission Runtime
Continua no ROS 2, mas agora exposto via control plane.

### 4. Safety Runtime
Continua no ROS 2, mas agora exposto via control plane.

### 5. Perception Runtime
Continua no ROS 2, mas agora exposto via control plane/read model.

### 6. Read Model
Responsável por:
- snapshot
- metrics
- events
- replay
- run query

### 7. Operator UI
Responsável por:
- intenção humana
- monitoramento
- acionamento de actions
- navegação operacional

## Componentes recomendados

### New or refactored
- `services/control-api/`
- `packages/shared-ts/src/actions/`
- `packages/shared-py/src/control_plane/`
- `packages/shared-py/src/scenario_contracts/`
- `apps/dashboard/src/features/control-plane/`

### Reutilizados
- `robotics/ros2_ws/src/drone_mission/`
- `robotics/ros2_ws/src/drone_safety/`
- `robotics/ros2_ws/src/drone_perception/`
- `robotics/ros2_ws/src/drone_px4/`
- `robotics/ros2_ws/src/drone_telemetry/`
- `services/telemetry-api/`

## Architectural Rules

1. UI -> Control API -> adapters -> runtimes
2. UI nunca -> ROS 2 topic cru
3. UI nunca -> MAVSDK direto
4. Control API nunca substitui safety runtime
5. Read model não manda comando
6. Action model não depende do frontend

## Initial Refactor Moves

1. estabilizar o domínio
2. criar modelo de action
3. criar control plane skeleton
4. adaptar sim start/stop
5. adaptar scenario execution
6. adaptar mission actions
7. adaptar safety fault actions
8. plugar UI
