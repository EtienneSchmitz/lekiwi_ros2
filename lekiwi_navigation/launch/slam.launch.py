#!/usr/bin/env python3
"""SLAM / localisation pour le LeKiwi (adapte de adityakamath/lekiwi_ros2).

Gere les 3 modes via l'argument slam_mode :
    map      -> slam_toolbox en cartographie (construire une carte)
    localize -> slam_toolbox en localisation (re-utilise une carte serialisee)
    amcl     -> nav2_map_server + AMCL (localisation sur carte statique)

Tout-en-un (un seul terminal), Gazebo + SLAM + RViz :
    ros2 launch lekiwi_navigation slam.launch.py sim:=true
Sans sim:=true, lancer la sim a part : ros2 launch lekiwi_bringup sim_base.launch.py

Sauvegarde de la carte (mode map), une fois la zone parcourue en teleop :
    ros2 run nav2_map_server map_saver_cli -f \
        ~/ros2_bootcamp_ws/src/lekiwi_ros2/lekiwi_navigation/maps/<nom>/map
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            OpaqueFunction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import LifecycleNode, Node
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('rviz')
    headless = LaunchConfiguration('headless')
    use_sim = LaunchConfiguration('sim')
    slam_mode = LaunchConfiguration('slam_mode').perform(context)
    map_name = LaunchConfiguration('map_name').perform(context)

    if slam_mode not in ('map', 'localize', 'amcl'):
        raise RuntimeError(f"slam_mode '{slam_mode}' inconnu (map | localize | amcl).")
    if slam_mode in ('localize', 'amcl') and not map_name:
        raise RuntimeError(f"slam_mode:={slam_mode} requiert map_name (ex: map_name:=bootcamp).")

    pkg_nav = FindPackageShare('lekiwi_navigation').perform(context)
    # maps/ reste dans l'arbre source (non installe) -> realpath via le symlink-install
    pkg_src = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

    # Sim Gazebo optionnelle (sim:=true) -> publie /scan, sinon il faut la lancer a part.
    # Laissee a false par defaut pour que navigation.launch.py (qui inclut deja sa propre
    # sim) ne demarre pas Gazebo deux fois.
    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('lekiwi_bringup'),
                         'launch', 'sim_base.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time, 'headless': headless}.items(),
        condition=IfCondition(use_sim),
    )

    # RViz dedie SLAM (carte /map + LIDAR /scan), comme turtlebot3_cartographer.
    # Note : sans sim:=true, lancer la sim a part pour publier /scan.
    rviz = Node(
        package='rviz2', executable='rviz2', name='rviz2',
        arguments=['-d', os.path.join(pkg_nav, 'rviz', 'slam.rviz')],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    if slam_mode in ('map', 'localize'):
        slam_params = PathJoinSubstitution([
            FindPackageShare('lekiwi_navigation'), 'config', 'nav2', 'slam_toolbox.yaml',
        ])
        extra = {
            'use_sim_time': use_sim_time,
            'mode': {'map': 'mapping', 'localize': 'localization'}[slam_mode],
            'use_lifecycle_manager': True,
        }
        if slam_mode == 'localize':
            extra['map_file_name'] = os.path.join(pkg_src, 'maps', map_name, 'map')

        return [
            sim,
            LifecycleNode(
                package='slam_toolbox', executable='async_slam_toolbox_node',
                name='slam_toolbox', namespace='', output='screen',
                parameters=[slam_params, extra],
            ),
            Node(
                package='nav2_lifecycle_manager', executable='lifecycle_manager',
                name='lifecycle_manager_slam', output='screen',
                parameters=[{'use_sim_time': use_sim_time, 'autostart': True,
                             'node_names': ['slam_toolbox']}],
            ),
            rviz,
        ]

    # amcl : map_server + AMCL sur carte statique
    map_yaml = os.path.join(pkg_src, 'maps', map_name, 'map.yaml')
    return [
        sim,
        Node(
            package='nav2_map_server', executable='map_server', name='map_server',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time, 'yaml_filename': map_yaml}],
        ),
        Node(
            package='nav2_amcl', executable='amcl', name='amcl', output='screen',
            parameters=[f'{pkg_nav}/config/nav2/amcl.yaml', {'use_sim_time': use_sim_time}],
        ),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_localization', output='screen',
            parameters=[{'use_sim_time': use_sim_time, 'autostart': True,
                         'node_names': ['map_server', 'amcl']}],
        ),
        rviz,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('slam_mode', default_value='map',
                              description='map | localize | amcl'),
        DeclareLaunchArgument('map_name', default_value='',
                              description='Nom du sous-dossier maps/ pour localize/amcl.'),
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Horloge sim.'),
        DeclareLaunchArgument('rviz', default_value='true',
                              description='Lance RViz (carte + LIDAR). rviz:=false pour couper.'),
        DeclareLaunchArgument('sim', default_value='false',
                              description='true = lance aussi Gazebo (sim_base) pour tout-en-un.'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='true = Gazebo sans GUI (avec sim:=true).'),
        OpaqueFunction(function=launch_setup),
    ])
