# AGENTS.md

## Objetivo do repositório

Este repositório existe para construir um stack completo de autonomia de drone **100% em simulação**, usando:

- PX4 SITL
- Gazebo
- ROS 2
- MAVSDK
- OpenCV
- backend/dashboard para observabilidade

O objetivo atual **não** é operar hardware real. Toda implementação deve assumir **simulation-first**.

## Ordem de leitura obrigatória antes de qualquer mudança

1. `docs/PROJECT-SCOPE.md`
2. `docs/SIMULATION-ARCHITECTURE.md`
3. `docs/PROJECT-ARCHITECTURE.md`
4. `docs/MONOREPO-STRUCTURE.md`
5. `docs/DEVELOPMENT-STANDARDS.md`
6. `docs/TESTING-AND-FAILURE-MODEL.md`
7. `docs/CHECKLIST-FRAMEWORK.md`

## Regras globais

1. Não tratar o projeto como um script único; tratar como sistema distribuído de robótica.
2. PX4 é o dono do voo.
3. ROS 2 é o middleware principal.
4. MAVSDK é a camada principal para cenários e controle programático de alto nível.
5. O simulador é ambiente externo; o monorepo o orquestra.
6. Toda feature relevante deve ter documentação, testes e critério de aceite.
7. Nenhum agente pode declarar prontidão para hardware real.
8. Nenhum agente pode tomar decisões de safety crítica sem revisão humana.
9. Não misturar regras de missão com dashboard.
10. Não misturar lógica de safety com lógica de missão no mesmo módulo, salvo justificativa explícita.

## Padrão mínimo de entrega

Toda entrega deve conter:

- arquivos alterados
- resumo do que foi implementado
- comandos de validação
- limitações conhecidas
- atualização documental, se a mudança afetar arquitetura/fluxo/testes

## Estrutura operacional esperada

- `docs/`
- `.agents/`
- `.codex/skills/`
- `robotics/`
- `simulation/`
- `scripts/`
- `services/`
- `apps/`

## Delegação

Use os subagentes em `.agents/` e as skills em `.codex/skills/` quando o trabalho for especializado.

## Proibições

- não inventar nova arquitetura sem alinhar com `docs/PROJECT-ARCHITECTURE.md`
- não alterar paths fora do escopo do subagente sem justificar
- não omitir testes quando a lógica tiver comportamento verificável
- não introduzir dependências pesadas sem necessidade
