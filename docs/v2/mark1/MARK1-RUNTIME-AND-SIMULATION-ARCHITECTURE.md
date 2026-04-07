# Mark 1 Runtime and Simulation Architecture

## Objetivo
Unificar o lifecycle de simulação e torná-lo visível como produto.

## Runtime stack atual
- Gazebo
- PX4 SITL
- Micro XRCE-DDS Agent
- ROS 2 bringup
- MAVSDK runner
- Telemetry API
- Dashboard

## Runtime stack Mark 1
O stack físico/simulado continua parecido, mas o lifecycle passa a ser exposto via Control Plane.

## Runtime modes

### Visual
- abre Gazebo com GUI
- permite observação humana direta

### Headless
- usado em smoke/CI/runtime non-visual

## Session lifecycle
1. `simulation.start`
2. preflight
3. PX4/Gazebo/XRCE sobem
4. ROS 2 optional/expected components sobem
5. session vira `active`
6. control plane publica capability availability
7. cenários e missões podem ser executados
8. `simulation.stop`
9. artifacts são fechados

## Runtime orquestration rules
- uma sessão ativa por default
- sessões simultâneas só se explicitamente suportadas no futuro
- toda run pertence a uma session
- toda run gera artifacts e status

## Environment strategy
### Official runtime proof
Continuar usando os validators oficiais e containerizados onde necessário.

### Official operator experience
Definir um caminho local visual suportado e documentado como experiência de produto, não apenas como side path.

## Recommended control-plane orchestration responsibilities
- checks de disponibilidade
- spawn/stop de runtime
- run creation
- action routing
- error normalization
- session status normalization
