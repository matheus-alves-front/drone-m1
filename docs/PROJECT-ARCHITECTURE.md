# PROJECT-ARCHITECTURE.md

## Princípio arquitetural

Este projeto deve ser tratado como um **sistema distribuído de robótica**, não como um script único.

## Camadas do sistema

### 1. Flight stack
Responsável por:
- estabilização
- modos de voo
- failsafes
- geofence
- missão de baixo nível
- execução do controle de voo

**Tecnologias:**
- PX4
- MAVLink

### 2. Simulação
Responsável por:
- mundo 3D
- física
- sensores simulados
- câmera simulada
- ambiente reproduzível

**Tecnologias:**
- Gazebo

### 3. Middleware de robótica
Responsável por:
- organizar o sistema em nodes
- transportar mensagens
- desacoplar módulos
- estruturar launchs e params

**Tecnologias:**
- ROS 2

### 4. Integração com autopilot
Responsável por:
- conversar com PX4
- ler estado do veículo
- enviar setpoints e comandos
- adaptar mensagens entre domínios

**Tecnologias:**
- uXRCE-DDS
- px4_msgs
- MAVSDK

### 5. Autonomia e missão
Responsável por:
- state machine
- tomada de decisão
- regras de patrulha
- interrupção e fallback
- coordenação entre percepção e comando

**Tecnologias:**
- ROS 2 nodes próprios
- Python

### 6. Percepção
Responsável por:
- ingestão de câmera
- pré-processamento
- detecção
- tracking
- geração de eventos

**Tecnologias:**
- OpenCV
- modelos de visão
- Isaac ROS (opcional depois)

### 7. Operação e observabilidade
Responsável por:
- telemetria
- dashboard
- logs
- replay
- armazenamento de métricas

**Tecnologias:**
- backend em Node ou Python
- frontend em React/Next
- websocket
- banco leve ou arquivos estruturados

## Regras de arquitetura

1. PX4 continua sendo o dono do voo.
2. ROS 2 é o middleware principal da autonomia.
3. MAVSDK é usado como API de alto nível e runner de cenários.
4. O código do domínio do projeto não deve depender diretamente de detalhes internos do PX4 quando isso puder ser abstraído.
5. Criar um pacote próprio de mensagens do domínio (`drone_msgs`) para reduzir acoplamento.
6. Os nodes devem ter responsabilidade única.

## Componentes principais sugeridos

- `px4_interface_node`
- `mission_manager_node`
- `safety_manager_node`
- `camera_input_node`
- `object_detector_node`
- `tracker_node`
- `telemetry_bridge_node`
- `scenario_monitor_node`

## Fluxo principal

1. PX4 SITL sobe
2. Gazebo sobe
3. XRCE Agent sobe
4. ROS 2 nodes sobem
5. MAVSDK runner inicia cenário
6. Mission manager coordena a lógica
7. Safety manager observa falhas
8. Perception pipeline gera eventos
9. Telemetry bridge publica estado
10. Dashboard consome e exibe
