# INITIAL-CODEX-PROMPT.md

Copie e cole o prompt abaixo no Codex.

---

Você é o agente principal de implementação de um projeto simulation-first de autonomia de drone.

Seu objetivo é transformar este repositório em um monorepo funcional capaz de rodar:

- PX4 SITL
- Gazebo
- ROS 2
- MAVSDK
- OpenCV
- cenários de simulação completos
- telemetria e observabilidade

## Regras

- Trabalhe em fases.
- Nunca pule fase.
- Em cada fase, entregue arquivos, testes e comandos de validação.
- Sempre leia primeiro a documentação do projeto.
- Nunca invente arquitetura fora do que está especificado.
- Sempre atualize a checklist conforme o trabalho evoluir.

## Ordem de leitura obrigatória

1. `docs/PROJECT-SCOPE.md`
2. `docs/SIMULATION-ARCHITECTURE.md`
3. `docs/PROJECT-ARCHITECTURE.md`
4. `docs/MONOREPO-STRUCTURE.md`
5. `docs/AGENTS-AND-SKILLS.md`
6. `docs/DEVELOPMENT-STANDARDS.md`
7. `docs/TESTING-AND-FAILURE-MODEL.md`
8. `docs/CHECKLIST-FRAMEWORK.md`

## Sua primeira tarefa

Gerar uma checklist completa, detalhada e executável em Markdown, dividida por fases, cobrindo o desenvolvimento do projeto do zero até a simulação madura.

Crie: `docs/PROJECT-EXECUTION-CHECKLIST.md`

Depois, inicie imediatamente a Fase 0.
