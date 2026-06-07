import os
from glob import glob

from setuptools import find_packages, setup

package_name = 'lekiwi_manipulation'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Etienne Schmitz',
    maintainer_email='contact@etienne-schmitz.com',
    description='Demo de manipulation mobile (nav -> pick) LeKiwi + SO-101.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'nav_then_pick = lekiwi_manipulation.nav_then_pick:main',
        ],
    },
)
