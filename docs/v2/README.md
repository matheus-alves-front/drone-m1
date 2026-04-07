# Docs V2

Esta pasta contém a documentação do refactor para a próxima geração do projeto.

## Estrutura

- `mark1/`  
  Implementação-alvo imediata: **Drone Control Platform**

- `mark2/`  
  Planejamento-alvo de próxima geração: **Advanced Robotics Platform**

## Ideia central

### Mark 1
Pegar o stack atual e transformá-lo em um **produto controlável por uma interface única**, com:

- control plane
- operator UI
- actions formais
- cenários homogêneos
- separação entre observabilidade e controle
- boa base para futura integração com IA/MCP

### Mark 2
Planejar a evolução para:

- múltiplos tipos de veículo
- payloads plugáveis
- atuadores plugáveis
- capability registry
- vehicle family abstraction
- plataforma robótica modular

## O que não fazer

- não implementar Mark 2 completo agora
- não matar o futuro simplificando o Mark 1
- não confundir interface visual com arquitetura de controle
- não acoplar tudo ao Gazebo, ao dashboard ou ao ROS 2 topic cru

## Documentos raiz de maior importância

- `REFACTOR-PRINCIPLES.md`
- `REFACTOR-TERMINOLOGY.md`
- `MARK1-TO-MARK2-COMPATIBILITY-RULES.md`
- `MASTER-IMPLEMENTATION-ROADMAP.md`
- `IMPLEMENTATION-ROTEIRO.md`
- `INITIAL-CODEX-REFACTOR-PROMPT.md`
