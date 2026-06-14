#!/usr/bin/env python3
"""Navigation autonome du LeKiwi en simulation (Jour 2).

Empile : sim Gazebo (lekiwi_bringup/sim_base) + SLAM/localisation (slam.launch.py)
         + Nav2 (nav2.launch.py) + RViz.

Exemples :
    # Cartographie + nav (defaut) : teleop pour cartographier, puis "Nav2 Goal"
    ros2 launch lekiwi_navigation navigation.launch.py

    # Localisation sur une carte sauvegardee (slam_toolbox)
    ros2 launch lekiwi_navigation navigation.launch.py slam_mode:=localize map_name:=bootcamp

    # Localisation AMCL sur carte statique
    ros2 launch lekiwi_navigation navigation.launch.py slam_mode:=amcl map_name:=bootcamp
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('lekiwi_bringup')
    nav_share = get_package_share_directory('lekiwi_navigation')

    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    slam_mode = LaunchConfiguration('slam_mode')
    map_name = LaunchConfiguration('map_name')
    use_rviz = LaunchConfiguration('rviz')

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(bringup_share, 'launch', 'sim_base.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time, 'headless': headless}.items(),
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'slam.launch.py')),
        # rviz:=false : navigation lance son propre RViz (nav.rviz) -> pas de double fenetre.
        launch_arguments={'use_sim_time': use_sim_time, 'slam_mode': slam_mode,
                          'map_name': map_name, 'rviz': 'false'}.items(),
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav_share, 'launch', 'nav2.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', os.path.join(nav_share, 'rviz', 'nav.rviz')],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='true = Gazebo sans GUI.'),
        DeclareLaunchArgument('slam_mode', default_value='map',
                              description='map | localize | amcl'),
        DeclareLaunchArgument('map_name', default_value='',
                              description='Sous-dossier maps/ pour localize/amcl.'),
        DeclareLaunchArgument('rviz', default_value='true'),
        sim,
        slam,
        nav2,
        rviz,
    ])
