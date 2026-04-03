from setuptools import find_packages, setup


package_name = "drone_perception"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=("test",)),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="matheusalves",
    maintainer_email="matheusalves@example.com",
    description="Perception pipeline nodes for the drone autonomy ROS 2 workspace.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "camera_input_node = drone_perception.camera_input_node:main",
            "object_detector_node = drone_perception.object_detector_node:main",
            "tracker_node = drone_perception.tracker_node:main",
        ],
    },
)
