"""Monde warehouse "pick & place" + manipulateur mobile LeKiwi + SO-101 (Gazebo Ionic).

Fin wrapper : inclut sim_full.launch.py avec world:=warehouse.sdf (monde + robot
combine + camera eye-in-hand + ponts /clock /scan /imu /wrist_camera/* + controleurs
+ EKF). Ajoute :
  - un ALIAS camera /wrist_camera/image -> /camera/image_raw (+ camera_info), pour
    coller au nom d'interface attendu par le detector du Jour 4 (arg camera_alias) ;
  - un spawn d'objet optionnel sur la station (arg spawn:=true).

Exemples :
    ros2 launch lekiwi_bringup warehouse_sim.launch.py
    ros2 launch lekiwi_bringup warehouse_sim.launch.py headless:=true
    ros2 launch lekiwi_bringup warehouse_sim.launch.py spawn:=true object_type:=cube_aruco aruco_id:=1

Les objets se spawnent ensuite a la demande (autre terminal) :
    ros2 launch lekiwi_bringup spawn_object.launch.py object_type:=waste_can
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    bringup_share = get_package_share_directory('lekiwi_bringup')
    world = os.path.join(bringup_share, 'worlds', 'warehouse.sdf')

    headless = LaunchConfiguration('headless')
    camera_alias = LaunchConfiguration('camera_alias')
    spawn = LaunchConfiguration('spawn')

    sim_full = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'sim_full.launch.py'])),
        launch_arguments={'world': world, 'headless': headless}.items(),
    )

    # Alias camera eye-in-hand -> nom d'interface /camera/image_raw (detector J4).
    # Re-ponte le meme topic gz sous /camera/* via ros_gz_bridge (pas de topic_tools).
    camera_alias_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='camera_alias_bridge',
        parameters=[{'config_file': os.path.join(
            bringup_share, 'config', 'bridge_camera_alias.yaml')}],
        condition=IfCondition(camera_alias), output='screen',
    )

    # Spawn optionnel d'un objet sur la station (laisse le temps a gz de monter).
    spawn_object = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'spawn_object.launch.py'])),
        launch_arguments={
            'object_type': LaunchConfiguration('object_type'),
            'color': LaunchConfiguration('color'),
            'aruco_id': LaunchConfiguration('aruco_id'),
        }.items(),
        condition=IfCondition(spawn),
    )
    delayed_spawn = TimerAction(period=8.0, actions=[spawn_object])

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false',
                              description='true = Gazebo serveur seul (sans GUI).'),
        DeclareLaunchArgument('camera_alias', default_value='true',
                              description='Relayer /wrist_camera/image vers /camera/image_raw.'),
        DeclareLaunchArgument('spawn', default_value='false',
                              description='true = spawner un objet sur la station au demarrage.'),
        DeclareLaunchArgument('object_type', default_value='cube_color',
                              description='Type d objet si spawn:=true.'),
        DeclareLaunchArgument('color', default_value='red',
                              description='Couleur du cube si object_type=cube_color.'),
        DeclareLaunchArgument('aruco_id', default_value='0',
                              description='ID ArUco si object_type=cube_aruco.'),
        sim_full,
        camera_alias_bridge,
        delayed_spawn,
    ])
