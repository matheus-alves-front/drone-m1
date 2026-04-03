# drone_msgs/msg

Mensagens internas do dominio publicadas pelo workspace ROS 2.

## Diretriz

As mensagens definidas aqui servem para desacoplar mission, safety, perception e telemetria dos detalhes de `px4_msgs`.

## Arquivos

- `VehicleState.msg`: estado operacional simplificado do veiculo vindo da bridge real com PX4
- `VehicleCommand.msg`: comando de alto nivel aceito pela bridge `drone_px4`
- `VehicleCommandStatus.msg`: ACK transacional de comando vindo do PX4
- `MissionStatus.msg`: progresso e terminalidade da state machine de missao
- `SafetyFault.msg`: fault injection e eventos sinteticos para safety
- `SafetyStatus.msg`: decisao consolidada do safety manager
- `VisionDetection.msg`: deteccao primaria publicada por `object_detector_node`
- `TrackedObject.msg`: estado persistente de tracking consumido por mission
- `PerceptionEvent.msg`: notificacao de transicoes de detector e tracker
- `PerceptionHeartbeat.msg`: watchdog minimo entre percepção e safety
