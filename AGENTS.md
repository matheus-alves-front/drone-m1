# AGENTS.md

## Objetivo desta fase

O repositório entrou em um ciclo de **refatoração orientada a produto/control plane**.

O objetivo já não é apenas manter um stack simulation-first tecnicamente correto.  
O objetivo agora é transformar o projeto em uma **plataforma controladora unificada do drone**, com uma superfície humana forte e uma superfície programática coerente, sem quebrar a futura evolução para uma plataforma robótica modular mais ampla.

## Leitura obrigatória antes de qualquer mudança

1. `docs/v2/README.md`
2. `docs/v2/REFACTOR-PRINCIPLES.md`
3. `docs/v2/REFACTOR-TERMINOLOGY.md`
4. `docs/v2/MARK1-TO-MARK2-COMPATIBILITY-RULES.md`
5. `docs/v2/IMPLEMENTATION-ROTEIRO.md`
6. `docs/v2/mark1/MARK1-SCOPE.md`
7. `docs/v2/mark1/MARK1-REQUIREMENTS.md`
8. `docs/v2/mark1/MARK1-SOFTWARE-ARCHITECTURE.md`
9. `docs/v2/mark1/MARK1-CONTROL-PLANE-ARCHITECTURE.md`
10. `docs/v2/mark1/MARK1-DOMAIN-MODEL.md`
11. `docs/v2/mark1/MARK1-ACTION-AND-CAPABILITY-CONTRACTS.md`
12. `docs/v2/mark1/MARK1-IMPLEMENTATION-CHECKLIST.md`
13. `docs/v2/mark2/MARK2-VISION.md`
14. `docs/v2/mark2/MARK2-SOFTWARE-ARCHITECTURE.md`

## Regras globais

### 1. O escopo não pode ser simplificado
- Não reduza o projeto para um dashboard read-only.
- Não reduza o projeto para scripts soltos.
- Não esconda ações de produto em tópicos ROS 2 crus.
- Não acople a interface humana diretamente a MAVSDK ou PX4.

### 2. Mark 1 e Mark 2 devem ser respeitados
- Mark 1 é o alvo de implementação agora.
- Mark 2 é o alvo de compatibilidade futura.
- Não implemente Mark 2 inteiro durante o Mark 1.
- Não quebre a compatibilidade do Mark 1 com o Mark 2.

### 3. O Control Plane é a peça central
Toda nova ação de produto deve tender a passar por uma superfície unificada de control plane.

### 4. Safety continua soberano
- Safety não depende da IA.
- Safety não mora no frontend.
- Safety não pode ser bypassado por conveniência.

### 5. Observabilidade e controle são camadas separadas
- Telemetry/Read Model não deve virar comando.
- Control API não deve virar dump de estado.

### 6. A UI não é dona da lógica
O frontend coordena intenção humana, mas não carrega a regra central de missão, safety ou execução.

### 7. LLM/IA não fala diretamente com PX4
A futura camada MCP/IA deve falar com actions/capabilities do control plane, nunca diretamente com PX4, MAVSDK cru ou ROS 2 topic cru.

## Formato mínimo de toda entrega

Toda entrega deve incluir:

1. resumo do objetivo da mudança
2. arquivos alterados
3. decisões tomadas
4. comandos de validação
5. limitações conhecidas
6. impacto em compatibilidade Mark 1 → Mark 2
7. atualização documental quando aplicável

## Quando dividir em subagentes

Use `.agents/` quando houver:
- múltiplas bounded contexts
- risco de conflito entre arquivos
- necessidade de isolamento de responsabilidade
- validações por fase diferentes

## Regra de aceite

Nenhuma fase é considerada concluída se faltar:
- validação
- atualização de docs
- explicitação de impacto no control plane
- explicitação de compatibilidade com Mark 2
