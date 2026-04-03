from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image

from drone_perception.image_ops import preprocess_bgr_frame, ros_image_to_bgr


class CameraInputNode(Node):
    def __init__(self) -> None:
        super().__init__("camera_input")

        self.declare_parameter("input_topic", "/simulation/camera/image_raw")
        self.declare_parameter("output_topic", "/drone/perception/preprocessed_image")
        self.declare_parameter("blur_kernel_size", 5)

        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        self._output_publisher = self.create_publisher(
            Image,
            str(self.get_parameter("output_topic").value),
            qos,
        )
        self.create_subscription(
            Image,
            str(self.get_parameter("input_topic").value),
            self._handle_image,
            qos,
        )

        self.get_logger().info(
            "camera_input initialized "
            f"(input_topic={self.get_parameter('input_topic').value}, "
            f"output_topic={self.get_parameter('output_topic').value})"
        )

    def _handle_image(self, msg: Image) -> None:
        frame_bgr = ros_image_to_bgr(msg)
        processed = preprocess_bgr_frame(
            frame_bgr,
            blur_kernel_size=int(self.get_parameter("blur_kernel_size").value),
        )

        image_msg = Image()
        image_msg.header = msg.header
        image_msg.height = int(processed.shape[0])
        image_msg.width = int(processed.shape[1])
        image_msg.encoding = "bgr8"
        image_msg.is_bigendian = 0
        image_msg.step = int(processed.shape[1] * processed.shape[2])
        image_msg.data = processed.tobytes()
        self._output_publisher.publish(image_msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = CameraInputNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
