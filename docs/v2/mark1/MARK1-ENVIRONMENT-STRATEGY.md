# Mark 1 Environment Strategy

## Problema atual
O projeto funciona, mas a experiência está distribuída entre:
- host local visual
- validators containerizados
- devcontainer parcial

## Estratégia do Mark 1

### 1. Baseline oficial de desenvolvimento
Continuar explícito e versionado.

### 2. Baseline oficial de prova runtime
Os validators oficiais continuam sendo a prova de runtime.

### 3. Experiência oficial de operação local
Deve existir um caminho visual e manual suportado como produto:
- start visual
- operator UI
- control actions
- mission/fault/perception

### 4. Bootstrap repetível
Deve existir um caminho único para preparar uma máquina nova no baseline oficial do Mark 1, sem depender de memória humana para instalar Python, ROS 2, Gazebo, Node.js, PX4 e caches auxiliares.

### 5. Orçamento de ambiente
O ambiente oficial precisa considerar disco e não só compatibilidade de pacotes.

- baseline local recomendado: Ubuntu 22.04 + ROS 2 Humble
- VM recomendada para operação visual/manual: 80 GB de disco
- abaixo de ~35 GB livres o ciclo de validacao tende a falhar por build/log/cache antes de falhar por código

## Resultado desejado
Uma pessoa nova no projeto deve conseguir responder:
- qual ambiente usar para desenvolvimento?
- qual ambiente usar para prova oficial?
- qual ambiente usar para operar visualmente?
- onde o Codex deve focar quando precisar validar?
