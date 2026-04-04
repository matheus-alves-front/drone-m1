# LOCAL-SIMULATION-GUIDE.md

## Objetivo

Explicar como instalar o ambiente local, subir o projeto no Gazebo, visualizar a simulacao e controlar o drone pelos caminhos oficiais do repositório.

## Baseline oficial

- Ubuntu 22.04
- ROS 2 Humble
- Gazebo Harmonic
- PX4 `v1.16.1`
- `px4_msgs` alinhado com `release/1.16`

Se voce estiver fora de Ubuntu 22.04, o caminho mais seguro continua sendo o devcontainer ou os validadores em Docker.

### Nota importante para Ubuntu 24.04

Se a sua maquina host estiver em Ubuntu 24.04, o caminho local mais simples e confiavel e:

- rodar `PX4 SITL + Gazebo Harmonic` nativamente no host
- rodar o smoke test MAVSDK na `.venv`
- rodar o stack ROS 2 do projeto dentro do devcontainer ou pelos validadores containerizados

Isso acontece porque o baseline oficial do projeto e `ROS 2 Humble`, e o Humble nao e o target oficial de binarios em Ubuntu 24.04. Em Ubuntu 24.04, o ROS 2 suportado oficialmente e o Jazzy, que nao e o baseline deste repositorio.

Os validadores containerizados ignoram a `.venv` do host quando sobem `scripts/sim/start.sh`. Isso e intencional: dentro do Docker eles devem usar o `python3` do container mais os pacotes instalados pelo proprio validador, para evitar conflito com a `.venv` local que voce usa para rodar Gazebo e MAVSDK no host.

## Caminhos de uso

### Caminho recomendado para validar o projeto

Usar os validadores oficiais do repositório:

```bash
bash scripts/bootstrap/validate-phase-0.sh
bash robotics/ros2_ws/scripts/validate-workspace.sh
bash scripts/sim/validate-phase-1-container.sh
bash scripts/scenarios/validate-phase-2-container.sh
bash robotics/ros2_ws/scripts/validate-phase-3-container.sh
bash robotics/ros2_ws/scripts/validate-phase-4-container.sh
bash robotics/ros2_ws/scripts/validate-phase-5-container.sh
bash robotics/ros2_ws/scripts/validate-phase-6-container.sh
bash robotics/ros2_ws/scripts/validate-phase-7.sh
bash scripts/ci/validate-phase-8.sh
```

Esse caminho cobre o bootstrap, o workspace ROS 2 e a prova do stack real com PX4 SITL + Gazebo Harmonic.

### Caminho recomendado para desenvolvimento local

Usar Ubuntu 22.04 com Gazebo Harmonic e ROS 2 Humble instalados nativamente, ou abrir o repositório no devcontainer.

## Instalacao local no Ubuntu 22.04

### 1. Dependencias base

```bash
sudo apt-get update
sudo apt-get install -y \
  git curl wget gnupg2 lsb-release software-properties-common \
  build-essential cmake ninja-build pkg-config \
  python3 python3-pip python3-venv
```

Instalar a dependencia Python exigida pelo configure do PX4:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r third_party/PX4-Autopilot/Tools/setup/requirements.txt
```

O `scripts/sim/start.sh` detecta automaticamente `.venv/bin/python` quando ela existe. Esse caminho tambem evita o bloqueio de `externally-managed-environment` em Ubuntu 24.04.

Esse passo e melhor do que instalar pacotes soltos, porque acompanha o `requirements.txt` oficial do PX4 e evita incompatibilidades como `empy 4.x`, que quebra o gerador do `v1.16.1`.

### 2. Gazebo Harmonic

Adicionar o repositório oficial do Gazebo:

```bash
sudo wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list >/dev/null
sudo apt-get update
sudo apt-get install -y \
  gz-harmonic \
  gz-sim8-cli \
  gz-tools2 \
  gz-transport13-cli
```

### 3. ROS 2 Humble

Adicionar o repositório oficial do ROS 2:

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list >/dev/null
sudo apt-get update
sudo apt-get install -y \
  ros-humble-ros-base \
  python3-colcon-common-extensions \
  python3-pytest \
  ros-humble-ament-lint-common
```

Adicionar o sourcing ao shell:

```bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
source /opt/ros/humble/setup.bash
```

### 4. OpenCV e dependencias do baseline

```bash
sudo apt-get install -y \
  bc \
  dmidecode \
  gstreamer1.0-libav \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-ugly \
  libeigen3-dev \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  libimage-exiftool-perl \
  libopencv-dev \
  libunwind-dev \
  libxml2-utils \
  protobuf-compiler
```

## Preparacao do repositório

```bash
git clone --recurse-submodules git@github.com:matheus-alves-front/drone-m1.git
cd drone-m1
git submodule update --init --recursive
```

Validar o bootstrap:

```bash
bash scripts/bootstrap/validate-phase-0.sh
bash robotics/ros2_ws/scripts/validate-workspace.sh
bash scripts/sim/validate-phase-1.sh
```

Preparar o cache local do `Micro XRCE-DDS Agent` usado pelo runtime:

```bash
bash scripts/sim/validate-phase-1-container.sh --check
bash scripts/sim/validate-phase-1-container.sh
```

Depois disso, o `scripts/sim/start.sh` consegue reutilizar automaticamente o binario cacheado em `.cache/phase-1/micro-xrce-agent/` mesmo que `MicroXRCEAgent` nao esteja instalado no `PATH` global.

Se o build do PX4 parar em `OpenCVConfig.cmake`, confirme que `libopencv-dev` esta instalado:

```bash
pkg-config --modversion opencv4
```

Se voce quiser usar camera/sensores com o plugin GStreamer do Gazebo, confirme tambem:

```bash
pkg-config --modversion gstreamer-1.0
pkg-config --modversion gstreamer-app-1.0
```

## Como subir a simulacao

### Modo oficial validado

Esse modo usa a orquestracao da Fase 1:

```bash
bash scripts/sim/start.sh
```

Parar:

```bash
bash scripts/sim/stop.sh
```

### Modo visual com Gazebo GUI

Para abrir o Gazebo e ver a simulacao acontecendo:

```bash
PHASE1_HEADLESS=0 bash scripts/sim/start.sh
```

Se voce estiver usando a `.venv` local, nao precisa ativar o shell a cada execucao: o script ja tenta usá-la automaticamente.

Se voce quiser forcar manualmente o binario do agent:

```bash
MICRO_XRCE_AGENT_BIN="$PWD/.cache/phase-1/micro-xrce-agent/build/MicroXRCEAgent" \
PHASE1_HEADLESS=0 \
bash scripts/sim/start.sh
```

Esse comando:

- sobe o `Micro XRCE-DDS Agent`
- sobe o `PX4 SITL`
- abre o Gazebo Harmonic com a simulacao `gz_x500`
- preserva a mesma `GZ_PARTITION` operacional do projeto

Parar:

```bash
bash scripts/sim/stop.sh
```

## Como ver o que esta acontecendo

### Logs do stack minimo

- `.sim-logs/phase-1/px4_sitl.log`
- `.sim-logs/phase-1/microxrce_agent.log`

### Topicos do Gazebo

Usar a mesma `GZ_PARTITION` do runtime:

```bash
export GZ_PARTITION=drone-sim-phase1
gz topic -l
gz service -l
```

Se voce subir com outra particao:

```bash
export GZ_PARTITION=<a-mesma-usada-no-start>
```

### Topicos ROS 2

Depois do bringup:

```bash
ros2 topic list
ros2 topic echo /drone/vehicle_state
ros2 topic echo /drone/mission_status
ros2 topic echo /drone/safety_status
ros2 topic echo /drone/perception/tracked_object
```

## Como subir o bringup ROS 2

Esse trecho assume um ambiente com ROS 2 Humble realmente disponivel. Se `source /opt/ros/humble/setup.bash` falhar na sua maquina, o runtime ROS 2 do baseline nao esta instalado localmente.

Nesse caso, use uma destas opcoes:

1. abrir o repositorio no devcontainer
2. rodar os validadores containerizados das fases ROS 2
3. usar uma maquina Ubuntu 22.04 para o fluxo nativo completo

No terminal do workspace:

```bash
source /opt/ros/humble/setup.bash
cd robotics/ros2_ws
colcon build
source install/setup.bash
ros2 launch drone_bringup bringup.launch.py
```

### Habilitar subsistemas

Somente bridge PX4:

```bash
ros2 launch drone_bringup bringup.launch.py
```

Missao:

```bash
ros2 launch drone_bringup bringup.launch.py enable_mission:=true mission_auto_start:=false
```

Missao + safety:

```bash
ros2 launch drone_bringup bringup.launch.py enable_mission:=true enable_safety:=true mission_auto_start:=false
```

Missao + safety + percepcao + telemetria:

```bash
ros2 launch drone_bringup bringup.launch.py \
  enable_mission:=true \
  enable_safety:=true \
  enable_perception:=true \
  enable_telemetry:=true \
  mission_auto_start:=false
```

## Como controlar o drone

### 1. Smoke test MAVSDK: takeoff e pouso

Com o stack minimo ja em execucao:

Instalar MAVSDK na mesma `.venv` local:

```bash
. .venv/bin/activate
python -m pip install mavsdk
```

```bash
bash scripts/scenarios/run_takeoff_land.sh --system-address udp://:14540 --output json
```

Esse e o jeito mais simples de ver o drone decolar e pousar no Gazebo.

### 2. Missao ROS 2: patrol_basic

Subir o bringup com missao:

```bash
ros2 launch drone_bringup bringup.launch.py enable_mission:=true mission_auto_start:=false
```

Em outro terminal:

```bash
source /opt/ros/humble/setup.bash
cd robotics/ros2_ws
source install/setup.bash
ros2 topic pub --once /drone/mission_command drone_msgs/msg/MissionCommand "{stamp: {sec: 0, nanosec: 0}, command: start}"
```

Observar:

```bash
ros2 topic echo /drone/mission_status
ros2 topic echo /drone/vehicle_state
```

### 3. Abort manual da missao

```bash
ros2 topic pub --once /drone/mission_command drone_msgs/msg/MissionCommand "{stamp: {sec: 0, nanosec: 0}, command: abort}"
```

### 4. Comando direto de veiculo

Exemplo de arm:

```bash
ros2 topic pub --once /drone/vehicle_command drone_msgs/msg/VehicleCommand "{command: arm, target_altitude_m: 0.0}"
```

Exemplo de disarm:

```bash
ros2 topic pub --once /drone/vehicle_command drone_msgs/msg/VehicleCommand "{command: disarm, target_altitude_m: 0.0}"
```

## Como ver percepcao e telemetria

### Percepcao

Subir bringup com percepcao:

```bash
ros2 launch drone_bringup bringup.launch.py enable_mission:=true enable_safety:=true enable_perception:=true mission_auto_start:=false
```

Publicar feed sintetico:

```bash
python3 robotics/ros2_ws/scripts/publish_sim_camera_stream.py
```

Observar:

```bash
ros2 topic echo /drone/perception/detection
ros2 topic echo /drone/perception/tracked_object
ros2 topic echo /drone/perception_heartbeat
```

### Telemetria e dashboard

Subir a API:

```bash
python3 -m venv .cache/telemetry-api-venv
source .cache/telemetry-api-venv/bin/activate
pip install -r services/telemetry-api/requirements.txt
PYTHONPATH=services/telemetry-api uvicorn telemetry_api.main:app --host 127.0.0.1 --port 8080
```

Subir o dashboard:

```bash
npm install --prefix apps/dashboard
npm run --prefix apps/dashboard dev
```

Abrir no navegador o endpoint mostrado pelo Vite, normalmente `http://127.0.0.1:5173`.

## Sequencia recomendada para uso manual

1. `bash scripts/bootstrap/validate-phase-0.sh`
2. `bash scripts/sim/validate-phase-1.sh`
3. `PHASE1_HEADLESS=0 bash scripts/sim/start.sh`
4. `colcon build` no workspace ROS 2
5. `ros2 launch drone_bringup bringup.launch.py enable_mission:=true enable_safety:=true enable_perception:=true enable_telemetry:=true mission_auto_start:=false`
6. rodar `bash scripts/scenarios/run_takeoff_land.sh --system-address udp://:14540 --output json` ou publicar `MissionCommand`
7. acompanhar Gazebo, `ros2 topic echo` e dashboard
8. `bash scripts/sim/stop.sh`

## Troubleshooting rapido

- Se `gz topic -l` nao enxergar nada, quase sempre e `GZ_PARTITION` divergente.
- Se o `start.sh` falhar, olhar `.sim-logs/phase-1/`.
- Se a missao nao avancar, observar `/drone/mission_status` e `/drone/vehicle_command_status`.
- Se a percepcao nao travar lock, observar `/drone/perception/tracked_object` e `/drone/perception_heartbeat`.
- Se o dashboard abrir sem dados, validar `GET /api/v1/health` e se o bringup foi iniciado com `enable_telemetry:=true`.

## Referencias oficiais

- Gazebo Harmonic installation: https://gazebosim.org/docs/harmonic/install_ubuntu
- ROS 2 Humble installation: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html
- PX4 ROS 2 user guide: https://docs.px4.io/main/en/ros2/user_guide
