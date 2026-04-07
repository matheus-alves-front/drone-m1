# Mark 1 Acceptance Report

## Objective

Registrar a decisão final de aceite do Mark 1 como plataforma controladora unificada do drone.

## Acceptance decision

- status: accepted
- decision date: `2026-04-07T03:55:10-03:00`
- basis: full terminal QA suite, final acceptance matrix and updated runbooks

## Accepted product surface

- Control Plane unificado por `services/control-api`
- Operator Console unificada por `apps/dashboard`
- actions formais para simulação, cenário, missão, veículo, safety e percepção
- read model separado por `services/telemetry-api`
- `session`, `run`, `events`, `metrics` e `replay` como conceitos explícitos de produto

## Acceptance evidence

- `docs/v2/mark1/MARK1-FINAL-QA-REPORT.md`
- `docs/v2/mark1/MARK1-FINAL-ACCEPTANCE-MATRIX.md`
- `services/control-api/README.md`
- `apps/dashboard/README.md`
- `docs/v2/mark1/MARK1-ENVIRONMENT-STRATEGY.md`

## Mark 1 to Mark 2 compatibility decision

- accepted
- rationale:
- o frontend continua falando com surfaces unificadas de control/read model
- missão, safety, veículo e percepção continuam atrás do control plane
- capabilities continuam descobríveis sem expor runtime cru
- nenhuma integração nova exige acoplamento direto da UI ou de automação a PX4, MAVSDK cru ou tópico ROS 2 cru

## Final statement

O Mark 1 está aceito como base operacional e programática do projeto. A evolução para o Mark 2 pode seguir sem retrabalho estrutural da superfície pública entregue aqui.
