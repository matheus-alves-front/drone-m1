# Robotics Platform V2 Refactor Package

Este pacote foi criado para ser copiado para a raiz do repositório atual e substituir a camada de direção do próximo ciclo do projeto.

## O que está aqui

- `docs/v2/`  
  Nova documentação do refactor, separada em `mark1` e `mark2`

- `AGENTS.md`  
  Regras globais para o Codex durante o refactor

- `.agents/`  
  Novos subagentes focados em control plane, runtime, UI, contracts, capabilities e QA

- `.codex/skills/`  
  Novas skills reutilizáveis para o ciclo de refatoração

## Como pensar o pacote

### Mark 1
Transforma o projeto atual em uma **plataforma controladora unificada do drone**, ainda simulation-first, mas já hardware-ready em termos de arquitetura.

### Mark 2
Planeja a evolução para uma **plataforma robótica modular mais ampla**, com capability registry, payloads, atuadores, múltiplos tipos de veículo e prontidão futura para MCP/tooling de IA.

## Ordem de leitura obrigatória

1. `docs/v2/README.md`
2. `docs/v2/REFACTOR-PRINCIPLES.md`
3. `docs/v2/MARK1-TO-MARK2-COMPATIBILITY-RULES.md`
4. `docs/v2/IMPLEMENTATION-ROTEIRO.md`
5. `docs/v2/mark1/MARK1-SCOPE.md`
6. `docs/v2/mark1/MARK1-REQUIREMENTS.md`
7. `docs/v2/mark1/MARK1-SOFTWARE-ARCHITECTURE.md`
8. `docs/v2/mark1/MARK1-CONTROL-PLANE-ARCHITECTURE.md`
9. `docs/v2/mark1/MARK1-IMPLEMENTATION-CHECKLIST.md`
10. `docs/v2/mark2/MARK2-VISION.md`
11. `docs/v2/mark2/MARK2-SOFTWARE-ARCHITECTURE.md`
12. `docs/v2/mark2/MARK2-ROADMAP.md`

## Checklist operacional

O bootstrap estrutural do repositório e a execução faseada continuam auditados em
`docs/PROJECT-EXECUTION-CHECKLIST.md`.

## Como aplicar

1. Copie este pacote para a raiz do repositório atual.
2. Faça backup dos agentes/skills antigos.
3. Substitua `AGENTS.md`, `.agents/` e `.codex/skills/` pelos desta versão.
4. Faça commit isolado só de documentação e governança.
5. Use o prompt em `docs/v2/INITIAL-CODEX-REFACTOR-PROMPT.md` no Codex.
6. Peça para ele gerar a board/checklist expandida a partir do código atual, sem mudar o escopo.
7. Só então comece a implementação do Mark 1.

## Resultado esperado

Ao final do ciclo do Mark 1, o projeto deve parecer um **produto operável** e não apenas um stack técnico em camadas.
