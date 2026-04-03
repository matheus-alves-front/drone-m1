"""Bringup entrypoint for the real Phase 3 ROS 2 graph."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    package_share = get_package_share_directory("drone_bringup")
    default_params_file = os.path.join(package_share, "config", "drone_px4.yaml")
    default_mission_params_file = os.path.join(package_share, "config", "drone_mission.yaml")
    default_perception_params_file = os.path.join(package_share, "config", "drone_perception.yaml")
    default_safety_params_file = os.path.join(package_share, "config", "drone_safety.yaml")
    default_telemetry_params_file = os.path.join(package_share, "config", "drone_telemetry.yaml")

    params_file_arg = DeclareLaunchArgument(
        "params_file",
        default_value=default_params_file,
        description="Path to the externalized parameter file for drone bringup.",
    )
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Whether the bridge should use ROS simulation time.",
    )
    enable_mission_arg = DeclareLaunchArgument(
        "enable_mission",
        default_value="false",
        description="Whether the mission manager node should be launched.",
    )
    mission_params_file_arg = DeclareLaunchArgument(
        "mission_params_file",
        default_value=default_mission_params_file,
        description="Path to the externalized mission parameter file.",
    )
    mission_auto_start_arg = DeclareLaunchArgument(
        "mission_auto_start",
        default_value="false",
        description="Whether the mission manager should auto-start once telemetry is connected.",
    )
    enable_perception_arg = DeclareLaunchArgument(
        "enable_perception",
        default_value="false",
        description="Whether the perception pipeline should be launched.",
    )
    perception_params_file_arg = DeclareLaunchArgument(
        "perception_params_file",
        default_value=default_perception_params_file,
        description="Path to the externalized perception parameter file.",
    )
    enable_safety_arg = DeclareLaunchArgument(
        "enable_safety",
        default_value="false",
        description="Whether the safety manager node should be launched.",
    )
    safety_params_file_arg = DeclareLaunchArgument(
        "safety_params_file",
        default_value=default_safety_params_file,
        description="Path to the externalized safety parameter file.",
    )
    enable_telemetry_arg = DeclareLaunchArgument(
        "enable_telemetry",
        default_value="false",
        description="Whether the telemetry bridge node should be launched.",
    )
    telemetry_params_file_arg = DeclareLaunchArgument(
        "telemetry_params_file",
        default_value=default_telemetry_params_file,
        description="Path to the externalized telemetry parameter file.",
    )

    px4_bridge = Node(
        package="drone_px4",
        executable="px4_bridge_node",
        name="px4_bridge",
        output="screen",
        parameters=[
            LaunchConfiguration("params_file"),
            {
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )
    mission_manager = Node(
        package="drone_mission",
        executable="mission_manager_node",
        name="mission_manager",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_mission")),
        parameters=[
            LaunchConfiguration("mission_params_file"),
            {
                "auto_start": ParameterValue(
                    LaunchConfiguration("mission_auto_start"),
                    value_type=bool,
                ),
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )
    camera_input = Node(
        package="drone_perception",
        executable="camera_input_node",
        name="camera_input",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_perception")),
        parameters=[
            LaunchConfiguration("perception_params_file"),
            {
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )
    object_detector = Node(
        package="drone_perception",
        executable="object_detector_node",
        name="object_detector",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_perception")),
        parameters=[
            LaunchConfiguration("perception_params_file"),
            {
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )
    tracker = Node(
        package="drone_perception",
        executable="tracker_node",
        name="tracker",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_perception")),
        parameters=[
            LaunchConfiguration("perception_params_file"),
            {
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )
    safety_manager = Node(
        package="drone_safety",
        executable="safety_manager_node",
        name="safety_manager",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_safety")),
        parameters=[
            LaunchConfiguration("safety_params_file"),
            {
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )
    telemetry_bridge = Node(
        package="drone_telemetry",
        executable="telemetry_bridge_node",
        name="telemetry_bridge",
        output="screen",
        condition=IfCondition(LaunchConfiguration("enable_telemetry")),
        parameters=[
            LaunchConfiguration("telemetry_params_file"),
            {
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"),
                    value_type=bool,
                ),
            },
        ],
    )

    return LaunchDescription([
        params_file_arg,
        use_sim_time_arg,
        enable_mission_arg,
        mission_params_file_arg,
        mission_auto_start_arg,
        enable_perception_arg,
        perception_params_file_arg,
        enable_safety_arg,
        safety_params_file_arg,
        enable_telemetry_arg,
        telemetry_params_file_arg,
        px4_bridge,
        mission_manager,
        camera_input,
        object_detector,
        tracker,
        safety_manager,
        telemetry_bridge,
    ])
