# Refactor Principles

## 1. Simulation-first, hardware-ready
O projeto continua 100% focado em simulação no runtime atual, mas a arquitetura já nasce para reduzir custo de uma futura V1 física.

## 2. Product/control-plane-first
O sistema deve evoluir de "stack técnico que funciona" para "plataforma controladora operável".

## 3. PX4 continua sendo o flight core
PX4 permanece como o dono do controle de voo, sensores aeronáuticos, modos de voo e failsafes básicos.

## 4. ROS 2 continua sendo o runtime modular
ROS 2 permanece como barramento e runtime de missão, safety, percepção e adaptação de domínio.

## 5. MAVSDK é adapter operacional, não cérebro
MAVSDK continua importante, mas como adapter de cenários/comandos de alto nível, não como superfície de produto final.

## 6. Safety é soberano
Safety não pode depender de frontend, IA ou improvisação do operador.

## 7. Controle e observabilidade são separados
- Command side: Control Plane / Actions
- Read side: Telemetry / Snapshot / Events / Replay

## 8. Capability-driven architecture
O sistema deve caminhar para um modelo em que ações e capacidades sejam explícitas e versionadas.

## 9. Plugin-friendly design
Payloads, capacidades e futuras famílias de veículo não podem exigir reescrita estrutural do sistema.

## 10. Human-first + machine-first
A mesma plataforma deve servir:
- operador humano
- automação técnica
- futura camada MCP/tool para IA

## 11. No hidden business logic
Nenhuma regra central pode ficar escondida em:
- scripts shell soltos
- callbacks de UI
- tópicos sem contrato
- wrappers ad hoc

## 12. Final validation is mandatory
O ciclo termina apenas com:
- integração completa
- QA completo
- validação final
- documentação operacional fechada
