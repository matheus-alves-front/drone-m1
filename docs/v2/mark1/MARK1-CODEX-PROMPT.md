# Mark 1 Codex Prompt

Use este prompt quando quiser que o Codex trabalhe diretamente na implementação do Mark 1, depois que a board expandida existir.

---

Você vai implementar o Mark 1 da Drone Control Platform a partir do estado atual do repositório.

## Antes de qualquer coisa
Leia:
- `docs/PROJECT-CURRENT-STATE-AUDIT.md`
- `docs/v2/README.md`
- `docs/v2/REFACTOR-PRINCIPLES.md`
- `docs/v2/MARK1-TO-MARK2-COMPATIBILITY-RULES.md`
- Todos os arquivos novos dentro de `docs/`
- todos os arquivos em `docs/v2/mark1/`
- todos os arquivos em `docs/v2/mark2/`
- `AGENTS.md`
- `.agents/`
- `.codex/skills/`

## Regra central
Você está implementando o Mark 1, não o Mark 2.

Mas toda decisão do Mark 1 deve continuar compatível com o Mark 2.

## Seu foco
Transformar o projeto atual em uma plataforma controladora unificada, com:
- control plane
- operator UI
- actions/capabilities formais
- execução homogênea de cenários
- missão, safety e veículo controláveis por superfície de produto
- telemetria e replay preservados
- QA terminal final

## Como trabalhar
- trabalhe em fases
- não pule fases
- sempre cite arquivos reais afetados
- sempre diga o impacto Mark 1 → Mark 2
- sempre entregue comandos de validação
- nunca simplifique o escopo

## Formato esperado a cada rodada
1. objetivo da fase
2. arquivos alterados
3. decisões tomadas
4. validações executadas
5. limitações conhecidas
6. impacto na compatibilidade com Mark 2
7. próximos passos
