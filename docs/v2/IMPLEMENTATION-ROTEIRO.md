# Implementation Roteiro

## Objetivo
Guiar a adoção do pacote V2 e a execução do refactor inteiro.

## Etapa 1 — Atualizar o repositório
1. criar uma branch dedicada do refactor
2. copiar `docs/v2/` para o repositório
3. substituir `AGENTS.md`
4. substituir `.agents/`
5. substituir `.codex/skills/`
6. fazer um commit isolado só de documentação/governança

## Etapa 2 — Congelar o ponto de partida
1. manter o estado atual do projeto preservado
2. confirmar que os validators atuais continuam rodando
3. não iniciar implementação antes de a board do refactor existir

## Etapa 3 — Gerar a board gigante com o Codex
1. usar `docs/v2/INITIAL-CODEX-REFACTOR-PROMPT.md`
2. pedir a board expandida a partir do código atual
3. exigir que a checklist seja:
   - faseada
   - enorme
   - detalhada
   - ligada a arquivos reais
   - sem mudar o escopo

## Etapa 4 — Revisar a board
Verificar:
- se o Mark 1 está coberto integralmente
- se o Mark 2 aparece apenas como planejamento e compatibilidade
- se a board não simplificou o control plane
- se há QA terminal no fim

## Etapa 5 — Executar o Mark 1 por fases
Ordem recomendada:
1. governança e limpeza estrutural
2. modelo de domínio e actions
3. Control API skeleton
4. runtime orchestration
5. unificação de cenário/mission control
6. unificação de safety control
7. read model/telemetry cleanup
8. operator UI shell
9. operator UI command surface
10. camera/perception operation
11. replay/run/session integration
12. QA terminal

## Etapa 6 — Fechar o Mark 1
Só fechar quando houver:
- sistema operável
- UI controladora
- API programática
- validação completa
- runbook operacional
- documentação final

## Etapa 7 — Congelar o Mark 2 como próximo ciclo
- manter a documentação completa do Mark 2 no repo
- usar o Mark 2 como regra de compatibilidade
- não puxar complexidade prematura para dentro do Mark 1

## Anti-padrões
- começar codando UI antes de modelar actions
- tratar scenario runner como control plane
- continuar operando tudo por scripts dispersos
- mover lógica crítica para o frontend
- usar "MCP" como justificativa para pular modelagem
