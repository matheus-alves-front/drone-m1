# Scenarios

Diretorio reservado para cenarios de simulacao, smoke tests e contratos de execucao.

## Intencao

- Descrever o que deve acontecer na simulação.
- Servir como ponte entre o runner MAVSDK e os objetivos do projeto.
- Registrar criterio de aceite, falhas esperadas e dependencias.

## Estrutura esperada

- `takeoff_land`
- `patrol_basic`
- `failsafe_gps_loss`
- `failsafe_rc_loss`
- `geofence_breach`

## Cenário inicial

- `takeoff_land.md` e o smoke test inicial da Fase 1.
- O cenário deve documentar o objetivo, os pre-requisitos e o criterio de sucesso.
- O arquivo existe para orientar a próxima fase de runner MAVSDK, nao para executar missão real ainda.

## Contrato minimo de um cenario

- Nome e objetivo
- Pre-requisitos
- Sequencia de passos
- Falhas injetadas, se houver
- Sinais observaveis
- Criterio de sucesso
- Criterio de falha
