import unittest
from types import SimpleNamespace

import numpy as np

from drone_perception.image_ops import preprocess_bgr_frame, ros_image_to_bgr


class TestImageOps(unittest.TestCase):
    def test_ros_image_to_bgr_supports_rgb8(self) -> None:
        rgb = np.zeros((8, 8, 3), dtype=np.uint8)
        rgb[:, :] = (255, 0, 0)
        msg = SimpleNamespace(
            width=8,
            height=8,
            encoding="rgb8",
            data=rgb.tobytes(),
        )

        bgr = ros_image_to_bgr(msg)

        self.assertEqual(bgr.shape, (8, 8, 3))
        self.assertEqual(tuple(int(v) for v in bgr[0, 0]), (0, 0, 255))

    def test_preprocess_bgr_frame_preserves_shape(self) -> None:
        frame = np.zeros((24, 32, 3), dtype=np.uint8)

        processed = preprocess_bgr_frame(frame, blur_kernel_size=4)

        self.assertEqual(processed.shape, frame.shape)


if __name__ == "__main__":
    unittest.main()
