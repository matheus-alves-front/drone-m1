# TESTING-AND-FAILURE-MODEL.md

## Objetivo

Definir como o projeto será validado em simulação e como falhas serão tratadas e testadas.

## Níveis de teste

1. Unit tests
2. Component tests
3. Integration tests
4. E2E simulation tests

## Cenários obrigatórios

- `takeoff_land`
- `patrol_basic`
- `failsafe_gps_loss`
- `failsafe_rc_loss`
- `geofence_breach`

## Falhas obrigatórias para simular

- perda de GPS
- perda de RC
- perda de data link
- violação de geofence
- travamento de node de percepção
- atraso excessivo no pipeline
- perda de comunicação com backend

## Materializacao atual da Fase 5

- `geofence_breach` e validado por telemetria real do veiculo no ambiente oficial
- `failsafe_gps_loss` e validado por `SafetyFault` injetado durante a patrulha no ambiente oficial
- `failsafe_rc_loss` e validado por `SafetyFault` injetado durante a patrulha no ambiente oficial
- `data_link_loss`, `perception_timeout` e `perception_latency` possuem regras implementadas no pacote `drone_safety` e cobertura local por testes de componente

## Materializacao atual da Fase 6

- `visual_lock_gate` e validado no ambiente oficial com `PX4 SITL + Gazebo Harmonic + Micro XRCE-DDS Agent + ROS 2`
- o feed sintetico entra por `/simulation/camera/image_raw`
- a prova oficial exige materializacao de `VisionDetection`, `TrackedObject` e `PerceptionHeartbeat`
- a missao so avanca de `hover` para `patrol` depois de observar `TrackedObject.tracked=true`
- `perception_timeout` e validado no ambiente oficial com abort de missao e comando de pouso disparados por `drone_safety`

## Materializacao atual da Fase 7

- `telemetry_bridge_node` e validado localmente com serializacao de envelopes, fila assincrona e transporte HTTP
- a API de telemetria valida ingest, persistencia em disco, `snapshot`, `metrics`, `events`, `runs`, `replay` e websocket
- o dashboard valida renderizacao do estado operacional e atualizacao por stream websocket
- a validacao oficial da fase exige `npm test` e `npm run build` do dashboard, alem dos testes Python de bridge e backend
- o artefato terminal da fase e `bash robotics/ros2_ws/scripts/validate-phase-7.sh`

## Materializacao atual da Fase 8

- a suite terminal `bash scripts/ci/validate-phase-8.sh` consolida bootstrap, fases locais e validacoes runtime
- `takeoff_land` e provado pelo validador runtime da Fase 2
- `patrol_basic` e provado pelo validador runtime da Fase 4
- `geofence_breach`, `failsafe_gps_loss` e `failsafe_rc_loss` continuam provados pelo validador runtime da Fase 5
- `perception_timeout` continua provado pelo validador runtime da Fase 6
- `data_link_loss` e `perception_latency` ficam cobertos por testes locais de componente em `drone_safety/test/test_rules.py`
- a perda de comunicacao com backend fica coberta por teste local de componente em `drone_telemetry/test/test_transport.py`
- o travamento do pipeline de percepcao continua materializado como perda de heartbeat, exercitada pela regra e pela prova runtime de `perception_timeout`
- a workflow `.github/workflows/simulation-maturity.yml` espelha esse contrato em CI

## Regra de isolamento para E2E

Os cenarios oficiais de safety precisam rodar com isolamento de runtime.

- um cenario oficial nao pode reutilizar o mesmo runtime mutado de PX4/Gazebo do cenario anterior
- cada caso deve subir e parar seu proprio stack minimo
- logs e artefatos devem ficar segregados por caso para facilitar diagnostico
- a mesma regra vale para os casos oficiais da Fase 6: `visual_lock_gate` e `perception_timeout`
