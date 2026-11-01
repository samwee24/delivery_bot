from glob import glob

from setuptools import find_packages, setup

package_name = "delivery_bot_slam"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="delivery_bot team",
    maintainer_email="samwee24@users.noreply.github.com",
    description="SLAM support: covariance relay, trajectory recorder, explore/replay",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "odom_covariance_relay = delivery_bot_slam.odom_covariance_relay:main",
            "trajectory_recorder = delivery_bot_slam.trajectory_recorder:main",
        ],
    },
)
