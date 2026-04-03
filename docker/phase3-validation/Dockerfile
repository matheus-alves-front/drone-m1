ARG PHASE3_CONTAINER_BASE_IMAGE=drone-sim-phase1-harmonic:latest
FROM ${PHASE3_CONTAINER_BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y \
 && apt-get install -y --no-install-recommends curl gnupg2 lsb-release software-properties-common \
 && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | gpg --dearmor -o /usr/share/keyrings/ros-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) main" > /etc/apt/sources.list.d/ros2.list \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends \
      python3-colcon-common-extensions \
      python3-pytest \
      ros-humble-ament-lint-common \
      ros-humble-ros-base \
 && rm -rf /var/lib/apt/lists/*
