from setuptools import find_packages, setup


package_name = "drone_safety"

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
    description="Safety manager node for the drone autonomy ROS 2 workspace.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "safety_manager_node = drone_safety.safety_manager_node:main",
        ],
    },
)
