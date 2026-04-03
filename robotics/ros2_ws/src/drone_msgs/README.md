# drone_msgs

Pacote de interfaces do dominio para o workspace ROS 2 do projeto.

## Papel

- reduzir acoplamento do dominio com detalhes internos do PX4
- expor o estado operacional do veiculo em um contrato simples e estavel
- concentrar comandos de alto nivel que mission, safety e telemetria possam reutilizar
- concentrar eventos de safety e heartbeat de percepção do dominio
- concentrar os contratos de percepção que mission e safety consomem sem depender de OpenCV

## Interfaces atuais

- `msg/VehicleState.msg`
- `msg/VehicleCommand.msg`
- `msg/VehicleCommandStatus.msg`
- `msg/MissionStatus.msg`
- `msg/SafetyFault.msg`
- `msg/SafetyStatus.msg`
- `msg/VisionDetection.msg`
- `msg/TrackedObject.msg`
- `msg/PerceptionEvent.msg`
- `msg/PerceptionHeartbeat.msg`

## Observação

As mensagens continuam pequenas, mas agora o pacote ja cobre estado do veiculo, ACK de comando, progresso de missao, percepcao e contratos de safety sem expor `px4_msgs` diretamente para o resto do dominio.
