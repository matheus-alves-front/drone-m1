# drone_safety

Pacote de safety do dominio ROS 2 do projeto.

## Papel

- concentrar politica de safety sem misturar regra de missao
- observar telemetria real do veiculo, estado de missao e falhas injetadas
- decidir abort, `land` e `return_to_home` no dominio
- publicar um contrato explicito de safety para observabilidade

## Interfaces principais

- consome:
  - `/drone/vehicle_state`
  - `/drone/mission_status`
  - `/drone/safety_fault`
  - `/drone/perception_heartbeat`
- publica:
  - `/drone/safety_status`
  - `/drone/mission_command`
  - `/drone/vehicle_command`

## Regras implementadas

- `px4_failsafe_active`
- `geofence_breach`
- `gps_loss`
- `rc_loss`
- `data_link_loss`
- `perception_timeout`
- `perception_latency`

## Observacao operacional

O node nao toma decisoes durante o bootstrap da missao ainda no solo. A janela de monitoramento de safety fica ativa quando o veiculo esta armado ou quando a missao esta ativa e o veiculo ja saiu do estado pousado.
