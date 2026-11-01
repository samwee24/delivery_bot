from glob import glob

from setuptools import find_packages, setup

package_name = 'delivery_bot_drivers'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='delivery_bot team',
    maintainer_email='samwee24@users.noreply.github.com',
    description='L298N motor node and MPU6050 IMU node',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'motor_node = delivery_bot_drivers.motor_node:main',
            'imu_node = delivery_bot_drivers.imu_node:main',
        ],
    },
)
