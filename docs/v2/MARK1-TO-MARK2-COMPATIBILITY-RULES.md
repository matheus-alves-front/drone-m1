# Mark 1 to Mark 2 Compatibility Rules

## Objetivo
Garantir que o Mark 1 seja implementado de forma completa sem travar a evolução para o Mark 2.

## Regras obrigatórias

### 1. Não modelar tudo como "drone-only"
Mesmo no Mark 1, prefira nomes que deixem abertura para:
- vehicle
- mission
- capability
- payload
- actuator
- control plane

Evitar excessos como:
- `super_drone_manager_everything.py`
- `dashboard_direct_px4_client.ts`

### 2. Não expor ROS 2 topic cru como API de produto
ROS 2 topic pode continuar existindo internamente, mas a superfície de produto deve ser action-driven.

### 3. Não acoplar frontend diretamente a ROS 2 ou MAVSDK
UI fala com Control API.
Adapters falam com ROS 2 / MAVSDK / shell.

### 4. Não confundir cenário com executor
Cenário precisa ser:
- contrato
- executor
- action
- run/result

separadamente.

### 5. Não misturar telemetry/read model com command/control
Telemetry API é leitura.
Control API é comando.
Elas podem conversar, mas não devem virar uma coisa só.

### 6. Não enfiar safety no frontend ou em scripts
Safety continua como runtime/autonomia protegida.

### 7. Não deixar capability implícita
Toda capacidade relevante deve ter:
- nome estável
- descrição
- input
- output
- erro
- run semantics
- owner/runtime

### 8. Não fazer UI orientada a caso especial
UI deve ser orientada a entidades e actions, não a hacks pontuais.

### 9. Preparar o Mark 1 para hardware sem implementá-lo totalmente
Use:
- abstrações
- contratos
- drivers/adapters
- interfaces

Evite:
- lógica amarrada ao simulador em todo lugar

### 10. Toda fase do Mark 1 deve responder
- isso fecha o objetivo imediato?
- isso preserva o caminho do Mark 2?
