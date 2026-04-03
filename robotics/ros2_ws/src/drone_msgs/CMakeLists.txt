cmake_minimum_required(VERSION 3.8)
project(drone_msgs)

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/MissionCommand.msg"
  "msg/MissionStatus.msg"
  "msg/PerceptionEvent.msg"
  "msg/PerceptionHeartbeat.msg"
  "msg/SafetyFault.msg"
  "msg/SafetyStatus.msg"
  "msg/TrackedObject.msg"
  "msg/VehicleCommand.msg"
  "msg/VehicleCommandStatus.msg"
  "msg/VehicleState.msg"
  "msg/VisionDetection.msg"
  DEPENDENCIES builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
