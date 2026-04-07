# Initial Codex Refactor Prompt

Copie e cole este prompt no Codex.

---

Quero que você faça a transição deste repositório para um novo ciclo de refatoração orientado a produto/control plane.

## Contexto

O projeto atual já tem um stack simulation-first completo e auditado:
- PX4 SITL
- Gazebo
- ROS 2
- MAVSDK
- missão
- safety
- percepção
- telemetria
- dashboard

Agora o objetivo mudou.

Não queremos apenas um drone arquiteturalmente correto.
Queremos transformar o projeto em uma **plataforma controladora unificada do drone**, com:
- interface humana intuitiva
- interface programática consistente
- cenários e ações homogêneos
- control plane central
- compatibilidade explícita com uma futura plataforma robótica modular mais ampla

## Escopo

### Mark 1
Implementação real desta rodada:
- Drone Control Platform
- control plane
- operator UI
- actions/capabilities formais
- simulação controlável por uma superfície unificada
- QA terminal completo

### Mark 2
Planejamento compatível:
- plataforma robótica modular
- capability registry
- payloads
- actuators
- múltiplos tipos de veículo
- MCP readiness
- hardware readiness

Você NÃO deve implementar o Mark 2 agora.
Você deve implementar o Mark 1 já respeitando as regras de compatibilidade com o Mark 2.

## Leitura obrigatória

1. `docs/PROJECT-CURRENT-STATE-AUDIT.md`
2. `docs/v2/README.md`
3. `docs/v2/REFACTOR-PRINCIPLES.md`
4. `docs/v2/REFACTOR-TERMINOLOGY.md`
5. `docs/v2/MARK1-TO-MARK2-COMPATIBILITY-RULES.md`
6. `docs/v2/IMPLEMENTATION-ROTEIRO.md`
7. todos os arquivos em `docs/v2/mark1/`
8. todos os arquivos em `docs/v2/mark2/`
9. `AGENTS.md`
10. `.agents/`
11. `.codex/skills/`

## Sua tarefa inicial

Crie uma checklist gigantesca e executável do refactor, baseada NO CÓDIGO ATUAL, sem alterar o escopo.

Arquivo de saída:
`docs/v2/MARK1-REFATOR-EXECUTION-BOARD.md`

Essa board deve:
- usar o código atual como ponto de partida
- cobrir o Mark 1 inteiro
- respeitar o Mark 2 como compatibilidade
- detalhar fases, subfases, tarefas e critérios de aceite
- mapear arquivos reais que serão tocados
- identificar gaps na checklist inicial
- expandir a checklist sem simplificar o objetivo

## Regras da board

Cada fase deve incluir:
- objetivo
- escopo
- arquivos/produtos afetados
- tarefas detalhadas
- dependências
- subagente líder
- skills recomendadas
- validações
- critérios de pronto
- risco/atenção
- impacto Mark 1 → Mark 2

## Depois de gerar a board

Você deve:
1. resumir a estratégia da board
2. identificar o primeiro bloco de implementação
3. esperar confirmação antes de implementar

## Regras adicionais

- não altere o escopo
- não converta o projeto de volta para "scripts + dashboard read-only"
- não esconda control plane dentro de wrappers ad hoc
- não implemente features do Mark 2 fora do necessário para compatibilidade
- não comece pela UI antes de estabilizar domínio, actions e control plane
