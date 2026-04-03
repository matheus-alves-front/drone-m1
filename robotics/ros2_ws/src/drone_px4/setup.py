from setuptools import find_packages, setup


package_name = "drone_px4"

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
    description="PX4 adapter boundary for the drone autonomy ROS 2 workspace.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "px4_bridge_node = drone_px4.px4_bridge_node:main",
        ],
    },
)
