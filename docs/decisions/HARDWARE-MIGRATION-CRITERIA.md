# HARDWARE-MIGRATION-CRITERIA.md

## Objetivo

Registrar de forma explicita o que ainda precisa existir antes de qualquer migracao futura para hardware real.

## Estado atual

- O projeto esta pronto para simulacao madura.
- O projeto nao esta pronto para hardware real.
- Nenhuma entrega desta fase altera a regra simulation-first do repositorio.

## Criterios minimos antes de qualquer piloto de hardware

1. Revisao humana formal da arquitetura de safety.
2. Procedimento de kill switch e desarme de emergencia fora do software de missao.
3. Validacao de estimator, GPS, IMU e magnetometro em ambiente real.
4. Politica de bateria, perda de enlace e degradacao revisada para hardware.
5. HIL ou bancada intermediaria antes de voo livre.
6. Telemetria e observabilidade adaptadas para rede e tempos reais.
7. Revisao de limites fisicos de geofence, altitude e velocidade.
8. Runbooks operacionais especificos de hardware.
9. Lista de componentes, firmware, alimentacao e redundancia documentada.
10. Critico: nenhuma regra de safety pode ser promovida para hardware sem revisao humana explicita.

## O que a simulacao madura ja entrega

- reproducibilidade de boot do stack
- cenarios obrigatorios consolidados
- falhas simuladas observaveis
- operacao e replay auditaveis
- CI cobrindo estrutura e cenarios essenciais

## O que ainda falta para hardware

- integracao com sensores, controladores e enlace reais
- tuning fisico do veiculo
- validacao ambiental e regulatoria
- validacao humana de safety critica
- runbooks e planos de incidente para campo

## Regra de comunicacao

Qualquer documento, agente ou dashboard do projeto deve continuar afirmando explicitamente que o estado atual e `simulation-first`.
