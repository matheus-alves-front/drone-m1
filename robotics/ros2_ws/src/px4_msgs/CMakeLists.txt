cmake_minimum_required(VERSION 3.5)

project(px4_msgs)

list(INSERT CMAKE_MODULE_PATH 0 "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
	add_compile_options(-Wall -Wextra)
endif()

find_package(ament_cmake REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

# ##############################################################################
# Generate ROS messages, ROS2 interfaces and IDL files #
# ##############################################################################

# Build only the PX4 interfaces exercised by the current phases.
# The source tree stays aligned with release/1.16, but the workspace compiles
# the minimal runtime subset required by `drone_px4` and the phase validators.
set(PX4_MSGS
  "msg/FailsafeFlags.msg"
  "msg/GotoSetpoint.msg"
  "msg/VehicleCommand.msg"
  "msg/VehicleCommandAck.msg"
  "msg/VehicleControlMode.msg"
  "msg/VehicleGlobalPosition.msg"
  "msg/VehicleLandDetected.msg"
  "msg/VehicleLocalPosition.msg"
  "msg/VehicleStatus.msg"
)

set(PX4_SRVS)

# Generate introspection typesupport for C and C++ and IDL files
rosidl_generate_interfaces(${PROJECT_NAME}
	${PX4_MSGS}
	${PX4_SRVS}
	DEPENDENCIES builtin_interfaces
	ADD_LINTER_TESTS
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
