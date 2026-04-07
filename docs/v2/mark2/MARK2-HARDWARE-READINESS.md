# Mark 2 Hardware Readiness

## Objetivo
Deixar o caminho para uma futura V1 real aberto sem comprometer o foco simulation-first atual.

## Guiding statement
A plataforma não será operada no mundo real nesta rodada, mas deve ser arquitetada para reduzir custo de transição futura.

## O que precisa existir
- abstração de driver
- separação sim vs hardware
- contratos estáveis
- safety runtime independente
- action model estável
- replay/audit trail
- capability declaration
- payload/actuator interfaces

## O que deve continuar fora do runtime atual
- deployment físico final
- tuning físico real
- validação aeronáutica real
- certificação real
- runbooks de operação em campo

## Resultado desejado
Se um próximo ciclo quiser perseguir uma V1 real, o software já estará mais perto de:
- trocar adapters
- integrar hardware drivers
- endurecer safety
- endurecer operations
do que de "reescrever tudo".
