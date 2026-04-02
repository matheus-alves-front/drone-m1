# REPOSITORY-FILE-TREE-EXPLAINED.md

## Objetivo

Este documento explica:

1. a estrutura atual do repositório
2. o que cada arquivo e pasta significa
3. como essas peças se conectam
4. quais são os primeiros passos práticos para começar a desenvolver com o Codex

Este arquivo deve ser usado como **guia operacional de entrada** no projeto.

---

## Visão geral

O repositório foi estruturado em quatro blocos principais:

1. **`docs/`**  
   Documentação estratégica e técnica do projeto

2. **`AGENTS.md`**  
   Regras globais para o comportamento do Codex no repositório

3. **`.agents/`**  
   Perfis dos subagentes, com escopos e responsabilidades

4. **`.codex/skills/`**  
   Skills reutilizáveis, com instruções e workflows especializados

A ideia é simples:

- `docs/` define **o projeto**
- `AGENTS.md` define **como o Codex deve se comportar**
- `.agents/` define **quem faz o quê**
- `.codex/skills/` define **como executar tarefas especializadas com consistência**

---

## File tree explicado

```text
repo/
├── README.md
├── AGENTS.md
├── docs/
│   ├── PROJECT-SCOPE.md
│   ├── PROJECT-ARCHITECTURE.md
│   ├── SIMULATION-ARCHITECTURE.md
│   ├── MONOREPO-STRUCTURE.md
│   ├── AGENTS-AND-SKILLS.md
│   ├── DEVELOPMENT-STANDARDS.md
│   ├── TESTING-AND-FAILURE-MODEL.md
│   ├── CHECKLIST-FRAMEWORK.md
│   ├── INITIAL-CODEX-PROMPT.md
│   ├── SUBAGENT-PROMPTS.md
│   ├── PHASE-OWNERSHIP-MATRIX.md
│   └── SIMULATION-STACK-DECISIONS.md
├── .agents/
│   ├── architecture-agent.md
│   ├── repo-bootstrap-agent.md
│   ├── px4-vendor-agent.md
│   ├── simulation-orchestrator-agent.md
│   ├── ros2-workspace-agent.md
│   ├── px4-interface-agent.md
│   ├── mission-agent.md
│   ├── safety-agent.md
│   ├── perception-agent.md
│   ├── telemetry-agent.md
│   ├── dashboard-agent.md
│   ├── ci-agent.md
│   └── qa-safety-agent.md
└── .codex/
    └── skills/
        ├── simulation-orchestrator/
        │   └── SKILL.md
        ├── px4-integration/
        │   └── SKILL.md
        ├── ros2-workspace/
        │   └── SKILL.md
        ├── mission-system/
        │   └── SKILL.md
        ├── safety-system/
        │   └── SKILL.md
        ├── perception-pipeline/
        │   └── SKILL.md
        ├── telemetry-observability/
        │   └── SKILL.md
        └── dashboard-operations/
            └── SKILL.md
```

---

## Arquivo por arquivo

---

### `README.md`

### O que é
Arquivo de entrada do projeto.

### Função
Explica rapidamente:
- o objetivo do repositório
- a stack principal
- quais documentos são mais importantes
- como navegar no projeto

### Quando usar
Use sempre que alguém novo entrar no projeto ou quando você quiser revisar o panorama geral rapidamente.

---

### `AGENTS.md`

### O que é
Arquivo raiz de governança do Codex.

### Função
Define:
- regras globais de comportamento
- ordem obrigatória de leitura
- padrões de desenvolvimento
- limites de escopo
- expectativa de resposta dos agentes

### Papel no projeto
É o arquivo mais importante para o Codex entender **como operar dentro do repositório**.

### Quando usar
Sempre.  
Esse arquivo deve ser lido antes de qualquer execução mais séria do agente.

---

## Pasta `docs/`

Essa pasta contém a documentação estratégica e técnica do projeto.

---

### `docs/PROJECT-SCOPE.md`

### O que é
Escopo completo do projeto.

### Função
Define:
- objetivo do sistema
- o que o projeto deve fazer
- o que está fora do escopo
- critérios de sucesso
- restrições

### Quando usar
Leia primeiro quando quiser entender **o que estamos construindo**.

---

### `docs/PROJECT-ARCHITECTURE.md`

### O que é
Arquitetura técnica principal do sistema.

### Função
Define:
- camadas do sistema
- responsabilidades de cada bloco
- papel de PX4, ROS 2, MAVSDK, OpenCV
- recomendações de linguagem
- princípios de design

### Quando usar
Leia quando quiser entender **como o sistema é dividido tecnicamente**.

---

### `docs/SIMULATION-ARCHITECTURE.md`

### O que é
Documento que explica a arquitetura de simulação.

### Função
Define:
- quais processos compõem a simulação
- papel do PX4 SITL
- papel do Gazebo
- papel do ROS 2
- bridges e agentes
- fluxo de start do stack
- estrutura de cenários

### Quando usar
Leia quando quiser entender **onde a simulação entra e como ela roda**.

---

### `docs/MONOREPO-STRUCTURE.md`

### O que é
Documento da estrutura-alvo do monorepo.

### Função
Define:
- quais pastas existirão
- responsabilidade de cada pasta
- estratégia de vendor do PX4
- organização de apps, services, robotics e simulation

### Quando usar
Leia antes de criar estrutura de diretórios ou scaffolding.

---

### `docs/AGENTS-AND-SKILLS.md`

### O que é
Mapa conceitual de subagentes e skills.

### Função
Explica:
- quais agentes existem
- qual o papel de cada um
- quais skills eles precisam dominar
- políticas gerais de delegação

### Quando usar
Leia quando quiser entender **a estratégia de divisão de trabalho do Codex**.

---

### `docs/DEVELOPMENT-STANDARDS.md`

### O que é
Padrões de desenvolvimento do projeto.

### Função
Define:
- convenções para Python
- convenções para TypeScript
- padrões ROS 2
- regras para scripts bash
- critérios de pronto
- exigência de documentação e testes

### Quando usar
Leia antes de começar a implementar qualquer parte do projeto.

---

### `docs/TESTING-AND-FAILURE-MODEL.md`

### O que é
Modelo de testes e falhas.

### Função
Define:
- níveis de teste
- cenários obrigatórios
- falhas a simular
- métricas
- artefatos esperados
- critérios de aceite

### Quando usar
Leia quando estiver modelando testes, safety ou cenários E2E.

---

### `docs/CHECKLIST-FRAMEWORK.md`

### O que é
Esqueleto base da checklist de execução.

### Função
Divide o projeto em fases:
- bootstrap
- simulação mínima
- integração MAVSDK
- ROS 2 bridge
- missão
- safety
- percepção
- operação
- maturidade

### Quando usar
Leia quando quiser entender **a ordem correta de construção**.

---

### `docs/INITIAL-CODEX-PROMPT.md`

### O que é
Prompt inicial para o Codex.

### Função
Instrui o Codex a:
- ler a documentação do projeto
- gerar uma checklist executável
- criar o arquivo `docs/PROJECT-EXECUTION-CHECKLIST.md`
- iniciar a Fase 0

### Quando usar
Esse é o primeiro arquivo operacional que você deve colar no Codex.

---

### `docs/SUBAGENT-PROMPTS.md`

### O que é
Templates prontos de prompt para subagentes.

### Função
Ajuda a criar ou acionar subagentes com:
- escopo
- paths permitidos
- entregáveis
- comandos de validação

### Quando usar
Use quando quiser operar com subagentes de forma disciplinada.

---

### `docs/PHASE-OWNERSHIP-MATRIX.md`

### O que é
Matriz de responsabilidade por fase.

### Função
Mapeia:
- qual agente lidera cada fase
- quais agentes apoiam
- como evitar confusão de ownership

### Quando usar
Leia quando estiver distribuindo o trabalho entre múltiplos agentes.

---

### `docs/SIMULATION-STACK-DECISIONS.md`

### O que é
Documento de decisões de stack.

### Função
Explica por que a stack base é:
- PX4 SITL
- Gazebo
- ROS 2
- MAVSDK
- OpenCV

e em que momento Isaac ROS entra.

### Quando usar
Leia quando quiser revisar ou defender decisões arquiteturais da stack.

---

## Pasta `.agents/`

Essa pasta contém os perfis operacionais dos subagentes.

Cada arquivo dessa pasta representa um agente especializado.

---

### `.agents/architecture-agent.md`

### Função
Responsável por:
- arquitetura
- contratos
- fronteiras entre módulos
- coerência estrutural

### Use quando
Precisar revisar ou propor arquitetura.

---

### `.agents/repo-bootstrap-agent.md`

### Função
Responsável por:
- estrutura do monorepo
- setup inicial
- scripts base
- arquivos de bootstrap

### Use quando
Precisar criar a base do repositório.

---

### `.agents/px4-vendor-agent.md`

### Função
Responsável por:
- vendor do PX4
- pinagem de versão
- setup de integração inicial com simulação

### Use quando
Chegar a hora de trazer PX4 para o repo.

---

### `.agents/simulation-orchestrator-agent.md`

### Função
Responsável por:
- scripts de start/stop
- orquestração de processos
- integração entre PX4, Gazebo, XRCE e ROS 2

### Use quando
Precisar subir o stack de simulação completo.

---

### `.agents/ros2-workspace-agent.md`

### Função
Responsável por:
- workspace colcon
- pacotes ROS 2
- launch files
- params

### Use quando
Entrar na fase de estrutura robótica.

---

### `.agents/px4-interface-agent.md`

### Função
Responsável por:
- integração PX4 ↔ ROS 2
- uso de `px4_msgs`
- QoS
- tópicos do PX4
- adaptação de comandos

### Use quando
Precisar conectar seu domínio ao autopilot.

---

### `.agents/mission-agent.md`

### Função
Responsável por:
- mission manager
- state machine
- patrulha
- lógica de missão

### Use quando
Começar a automatizar comportamento do drone.

---

### `.agents/safety-agent.md`

### Função
Responsável por:
- geofence
- fallback
- abort
- watchdogs
- regras de safety

### Use quando
Entrar em fases de falha e proteção.

---

### `.agents/perception-agent.md`

### Função
Responsável por:
- pipeline de câmera
- OpenCV
- detector
- tracker
- eventos visuais

### Use quando
Começar a integrar visão computacional.

---

### `.agents/telemetry-agent.md`

### Função
Responsável por:
- bridge de telemetria
- persistência
- logs
- replay
- métricas

### Use quando
Precisar construir observabilidade.

---

### `.agents/dashboard-agent.md`

### Função
Responsável por:
- UI operacional
- visualização de missão
- monitoramento
- replay visual

### Use quando
Começar o dashboard.

---

### `.agents/ci-agent.md`

### Função
Responsável por:
- CI/CD
- lint
- build
- jobs automatizados
- execução de testes

### Use quando
Automatizar qualidade do repo.

---

### `.agents/qa-safety-agent.md`

### Função
Responsável por:
- cenários de validação
- critérios de aceite
- matriz de falhas
- checagem final de segurança em simulação

### Use quando
Validar maturidade de fase ou cenário.

---

## Pasta `.codex/skills/`

Essa pasta contém skills reutilizáveis.

A diferença entre **agente** e **skill** é:

- **agente** = papel/responsabilidade
- **skill** = conhecimento operacional reutilizável

---

### `.codex/skills/simulation-orchestrator/SKILL.md`

### Função
Explica como subir, parar e validar o stack de simulação.

### Quando usar
Sempre que o foco for boot do ambiente ou troubleshooting do startup.

---

### `.codex/skills/px4-integration/SKILL.md`

### Função
Explica padrões de integração com PX4.

### Quando usar
Ao trabalhar com autopilot, tópicos PX4 ou interface de comando.

---

### `.codex/skills/ros2-workspace/SKILL.md`

### Função
Explica como organizar o workspace ROS 2.

### Quando usar
Ao criar pacotes, nodes, launch files e params.

---

### `.codex/skills/mission-system/SKILL.md`

### Função
Explica como modelar missão, estados e patrulha.

### Quando usar
Ao implementar autonomia comportamental.

---

### `.codex/skills/safety-system/SKILL.md`

### Função
Explica como modelar safety, geofence, abort e recovery.

### Quando usar
Ao implementar fallback e reação a falhas.

---

### `.codex/skills/perception-pipeline/SKILL.md`

### Função
Explica como construir pipeline de câmera e percepção.

### Quando usar
Ao integrar OpenCV e eventos visuais.

---

### `.codex/skills/telemetry-observability/SKILL.md`

### Função
Explica como modelar telemetria, métricas, logs e replay.

### Quando usar
Ao construir a camada operacional do sistema.

---

### `.codex/skills/dashboard-operations/SKILL.md`

### Função
Explica como construir a interface operacional do projeto.

### Quando usar
Ao implementar UI de monitoramento e observabilidade.

---

## Como tudo isso se encaixa

### Camada 1 — definição do projeto
Arquivos:
- `docs/PROJECT-SCOPE.md`
- `docs/PROJECT-ARCHITECTURE.md`
- `docs/SIMULATION-ARCHITECTURE.md`

Esses arquivos dizem **o que estamos construindo e como pensamos o sistema**.

### Camada 2 — governança do Codex
Arquivos:
- `AGENTS.md`
- `.agents/*`
- `.codex/skills/*`

Esses arquivos dizem **como o Codex deve trabalhar dentro do projeto**.

### Camada 3 — execução
Arquivos:
- `docs/CHECKLIST-FRAMEWORK.md`
- `docs/INITIAL-CODEX-PROMPT.md`

Esses arquivos dizem **como começar e em que ordem construir**.

---

## Primeiros passos para desenvolver com o Codex

Aqui está a sequência recomendada.

---

### Passo 1 — validar que os arquivos estão na raiz certa

Confirme no repositório:

- `AGENTS.md` na raiz
- `.agents/` na raiz
- `.codex/skills/` na raiz
- `docs/` na raiz

Se isso estiver errado, o comportamento do Codex pode ficar inconsistente.

---

### Passo 2 — abrir e revisar os arquivos base

Revise manualmente, na seguinte ordem:

1. `docs/PROJECT-SCOPE.md`
2. `docs/SIMULATION-ARCHITECTURE.md`
3. `docs/PROJECT-ARCHITECTURE.md`
4. `docs/MONOREPO-STRUCTURE.md`
5. `AGENTS.md`
6. `docs/DEVELOPMENT-STANDARDS.md`

Objetivo:
- garantir que você concorda com o escopo
- garantir que a arquitetura faz sentido para você
- garantir que o stack escolhido está correto

---

### Passo 3 — usar o prompt inicial no Codex

Abra o arquivo:

- `docs/INITIAL-CODEX-PROMPT.md`

Copie e cole esse conteúdo no Codex.

Objetivo:
fazer o Codex gerar:

- `docs/PROJECT-EXECUTION-CHECKLIST.md`

Esse arquivo será a checklist detalhada real de execução.

---

### Passo 4 — revisar a checklist gerada

Antes de deixar o Codex implementar fases automaticamente, revise:

- se as fases estão na ordem certa
- se existe granularidade suficiente
- se os critérios de aceite por fase estão claros
- se o escopo não ficou amplo demais cedo demais

---

### Passo 5 — mandar o Codex iniciar pela Fase 0

A Fase 0 deve focar em:

- estrutura de diretórios
- arquivos de bootstrap
- scaffolding base
- scripts iniciais
- setup de Python/Node
- Makefile inicial
- documentação mínima de execução

Objetivo:
ter um repo pronto para receber os próximos blocos.

---

### Passo 6 — usar subagentes conscientemente

Quando a implementação começar a ficar grande, distribua por especialidade:

- bootstrap → `repo-bootstrap-agent`
- simulação → `simulation-orchestrator-agent`
- ROS 2 → `ros2-workspace-agent`
- PX4 → `px4-interface-agent`
- missão → `mission-agent`
- safety → `safety-agent`
- percepção → `perception-agent`
- telemetria → `telemetry-agent`
- UI → `dashboard-agent`

Não use vários agentes alterando a mesma área ao mesmo tempo sem revisão.

---

### Passo 7 — exigir sempre o mesmo formato de entrega

Para qualquer fase, peça sempre:

1. resumo da fase
2. arquivos criados ou alterados
3. comandos de validação
4. limitações conhecidas
5. próximos passos

Isso reduz erro e facilita revisão.

---

### Passo 8 — não pular para percepção cedo demais

A ordem recomendada continua sendo:

1. bootstrap
2. simulação mínima
3. MAVSDK
4. ROS 2 bridge
5. missão
6. safety
7. percepção
8. observabilidade forte
9. cenários avançados

Começar por visão cedo demais tende a gerar bagunça.

---

### Passo 9 — tratar simulação como produto

Desde cedo, exija:

- scripts reproduzíveis
- logs
- outputs
- artefatos
- cenários nomeados
- comandos claros

A simulação precisa ser executável como sistema, não como experimento manual.

---

### Passo 10 — congelar decisões por fase

Ao final de cada fase, registre:

- o que foi aceito
- o que ficou pendente
- o que mudou na arquitetura
- quais riscos sobraram

Isso evita que o Codex “reinvente” o projeto em cada iteração.

---

## Como eu recomendo operar no dia a dia

### Modo correto
- você define a fase
- você entrega contexto
- o Codex executa
- você revisa
- o Codex corrige
- a fase é fechada
- só então a próxima fase começa

### Modo errado
- pedir tudo ao mesmo tempo
- deixar o agente alterar qualquer pasta
- misturar bootstrap, missão, percepção e dashboard no mesmo ciclo
- não exigir testes e comandos de validação

---

## Primeiro comando real que eu recomendo

Seu primeiro passo operacional deve ser:

1. abrir `docs/INITIAL-CODEX-PROMPT.md`
2. colar no Codex
3. pedir explicitamente:

> Leia toda a documentação obrigatória, gere `docs/PROJECT-EXECUTION-CHECKLIST.md` e só então comece a implementar a Fase 0.

Esse é o ponto de partida certo.

---

## Resultado esperado desta etapa

Depois disso, você deverá ter:

- uma checklist completa
- a Fase 0 iniciada
- uma base concreta de repo
- um fluxo repetível de evolução por fase

Esse é o início correto para construir o projeto inteiro de forma ordenada com o Codex.
