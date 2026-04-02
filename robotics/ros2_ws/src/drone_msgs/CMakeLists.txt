cmake_minimum_required(VERSION 3.8)
project(drone_msgs)

find_package(ament_cmake REQUIRED)

install(DIRECTORY msg
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
