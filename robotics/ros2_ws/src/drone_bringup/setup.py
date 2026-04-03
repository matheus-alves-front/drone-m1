from glob import glob

from setuptools import find_packages, setup


package_name = "drone_bringup"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=("test",)),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["drone_bringup/launch/bringup.launch.py"]),
        (f"share/{package_name}/config", glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    zip_safe=True,
    maintainer="matheusalves",
    maintainer_email="matheusalves@example.com",
    description="Launch entrypoint for the drone autonomy ROS 2 workspace.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [],
    },
)
