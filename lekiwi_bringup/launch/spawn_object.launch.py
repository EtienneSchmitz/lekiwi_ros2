"""Spawn d'objets a saisir sur la station du monde warehouse (Gazebo Ionic).

Demarre :
  - le PONT DE SERVICES ros_gz (config/bridge_spawn.yaml) : expose cote ROS 2 les
    services gz /world/<world>/create et /remove ;
  - le noeud scripts/spawn_object.py avec les arguments choisis.

Le monde + le robot doivent deja tourner (warehouse_sim.launch.py ou sim_full.launch.py
world:=warehouse.sdf).

Exemples :
    ros2 launch lekiwi_bringup spawn_object.launch.py object_type:=cube_color color:=green
    ros2 launch lekiwi_bringup spawn_object.launch.py object_type:=cube_aruco aruco_id:=1
    ros2 launch lekiwi_bringup spawn_object.launch.py object_type:=waste_can count:=2
    ros2 launch lekiwi_bringup spawn_object.launch.py action:=respawn name:=pick_object_0
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            OpaqueFunction)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ARGS = [
    ('world', 'warehouse', 'Nom du monde gz (doit matcher bridge_spawn.yaml).'),
    ('object_type', 'cube_color',
     'cube_color | cube_aruco | waste_can | waste_bottle | waste_carton | sdf'),
    ('color', 'red', 'Couleur cube_color (red/green/blue/yellow ou "r g b a").'),
    ('class_id', '', 'Classe logique (vide => derivee du type/couleur).'),
    ('aruco_id', '0', 'ID du marqueur ArUco (= classe) pour cube_aruco.'),
    ('model_path', '', 'Chemin SDF si object_type=sdf.'),
    ('pose', '', 'Pose explicite "x y z [yaw]" (vide => aleatoire sur la station).'),
    ('count', '1', "Nombre d'objets a spawner."),
    ('name', '', "Nom d'entite (vide => pick_object_<i>)."),
    ('action', 'spawn', 'spawn | delete | respawn.'),
]


def _spawn_node(context, *_, **__):
    params = {
        'world': LaunchConfiguration('world').perform(context),
        'object_type': LaunchConfiguration('object_type').perform(context),
        'color': LaunchConfiguration('color').perform(context),
        'class_id': LaunchConfiguration('class_id').perform(context),
        'aruco_id': int(LaunchConfiguration('aruco_id').perform(context)),
        'model_path': LaunchConfiguration('model_path').perform(context),
        'pose': LaunchConfiguration('pose').perform(context),  # "x y z [yaw]" (vide => aleatoire)
        'count': int(LaunchConfiguration('count').perform(context)),
        'name': LaunchConfiguration('name').perform(context),
        'action': LaunchConfiguration('action').perform(context),
    }
    return [Node(package='lekiwi_bringup', executable='spawn_object.py',
                 name='object_spawner', output='screen', parameters=[params])]


def generate_launch_description():
    bringup_share = get_package_share_directory('lekiwi_bringup')
    bridge_file = os.path.join(bringup_share, 'config', 'bridge_spawn.yaml')

    # Resolution des modeles/textures (aruco_*.png, waste_*) par Gazebo.
    set_models_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.path.join(bringup_share, 'models'))

    service_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        name='spawn_service_bridge',
        parameters=[{'config_file': bridge_file}],
        output='screen',
    )

    return LaunchDescription(
        [DeclareLaunchArgument(n, default_value=d, description=h) for n, d, h in ARGS]
        + [set_models_path, service_bridge, OpaqueFunction(function=_spawn_node)]
    )
