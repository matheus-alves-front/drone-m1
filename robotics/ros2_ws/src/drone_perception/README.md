# drone_perception

Pipeline de percepção da Fase 6 para o workspace ROS 2 do projeto.

## Papel

- consumir feed de câmera simulada via ROS 2
- pré-processar frames antes da detecção
- detectar o alvo sintético do baseline de simulação
- rastrear o alvo em um tópico de domínio desacoplado
- publicar heartbeat e eventos de percepção para safety e observabilidade

## Nodes

- `camera_input_node`
  - consome `/simulation/camera/image_raw`
  - publica `/drone/perception/preprocessed_image`
- `object_detector_node`
  - consome `/drone/perception/preprocessed_image`
  - publica `/drone/perception/detection`
  - publica eventos de detector em `/drone/perception/event`
- `tracker_node`
  - consome `/drone/perception/detection`
  - publica `/drone/perception/tracked_object`
  - publica `/drone/perception/event`
  - publica `/drone/perception_heartbeat`

## Contrato com mission e safety

- `MissionManager` usa `/drone/perception/tracked_object` como fonte persistente de `visual lock`
- `PerceptionEvent` continua sendo usado para notificacao de `target_detected`, `target_missing`, `track_locked` e `track_lost`
- `SafetyManager` usa `/drone/perception_heartbeat` como watchdog da saude do pipeline
- nenhum consumidor de dominio recebe frame bruto ou detalhe interno de OpenCV

## Validação oficial da fase

```bash
bash robotics/ros2_ws/scripts/validate-phase-6-container.sh
```

## Limites arquiteturais

- o pacote nao conhece PX4 internamente
- o pacote nao mistura regras de missao ou safety com OpenCV
- missao e safety consomem apenas contratos ROS 2 de dominio, nunca frames brutos
