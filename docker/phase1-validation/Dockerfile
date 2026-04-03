ARG PHASE1_CONTAINER_BASE_IMAGE=px4io/px4-dev-base-jammy:latest
FROM ${PHASE1_CONTAINER_BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

# The validation image must stay aligned with the project baseline:
# Ubuntu 22.04 + Gazebo Harmonic, without relying on a preloaded Garden stack.
RUN apt-get update -y \
 && apt-get install -y --no-install-recommends ca-certificates gnupg lsb-release wget \
 && wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" > /etc/apt/sources.list.d/gazebo-stable.list \
 && apt-get update -y \
 && apt-get install -y --no-install-recommends \
      bc \
      dmidecode \
      gz-harmonic \
      gz-sim8-cli \
      gz-tools2 \
      gz-transport13-cli \
      gstreamer1.0-libav \
      gstreamer1.0-plugins-bad \
      gstreamer1.0-plugins-base \
      gstreamer1.0-plugins-good \
      gstreamer1.0-plugins-ugly \
      libeigen3-dev \
      libgstreamer-plugins-base1.0-dev \
      libimage-exiftool-perl \
      libopencv-dev \
      libunwind-dev \
      libxml2-utils \
      pkg-config \
      protobuf-compiler \
      python3-pip \
 && rm -rf /var/lib/apt/lists/*
