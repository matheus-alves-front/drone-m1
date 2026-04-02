# SIMULATION-ARCHITECTURE.md

## Objetivo

Definir claramente:
- qual simulador usar
- quais processos rodam
- como eles se conectam
- como o monorepo organiza tudo
- como subir e testar cenários

## Stack de simulação padrão

### Simulação recomendada
- PX4 SITL
- Gazebo
- ROS 2
- MAVSDK
- `ros_gz_bridge`
- Micro XRCE-DDS Agent

## Papel de cada peça

### PX4 SITL
Roda o autopilot em software.

### Gazebo
Roda o mundo, a física e os sensores simulados.

### ROS 2
Roda os módulos de autonomia, missão, safety e percepção.

### MAVSDK
Roda o controle de cenários, scripts E2E e harness de testes.

### XRCE Agent
Permite PX4 expor tópicos para ROS 2.

### ros_gz_bridge
Permite integrar tópicos do Gazebo com ROS 2, como câmera.

## Modelo mental certo

O simulador **não contém** o projeto.

O projeto:
- sobe o simulador
- conecta no simulador
- controla o simulador
- lê dados do simulador
- testa o comportamento no simulador

## Processos do stack

1. Gazebo
2. PX4 SITL
3. Micro XRCE-DDS Agent
4. ROS 2 bringup
5. Runner de cenário MAVSDK
6. Backend e dashboard

## Fluxo de execução

1. exportar paths do Gazebo
2. subir XRCE Agent
3. subir PX4 SITL + Gazebo
4. subir workspace ROS 2
5. subir bridges
6. executar cenário
7. coletar métricas e logs
8. validar asserts
