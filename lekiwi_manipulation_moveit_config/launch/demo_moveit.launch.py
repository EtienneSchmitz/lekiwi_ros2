"""Demo MoveIt 2 de la plateforme mobile : sim Gazebo + MoveIt + RViz.

Lance :
  - lekiwi_bringup/sim_full.launch.py  -> Gazebo + ros2_control (base + bras) + EKF
  - move_group                         -> planificateur MoveIt (groupe 'arm')
  - RViz MoveIt                        -> panneau MotionPlanning

MoveIt connait la pose de la base via la TF odom->base_footprint publiee par
l'EKF de sim_full (virtual joint planar du SRDF). La base reste pilotable par
teleop/Nav2 pendant que MoveIt planifie le bras.

Note locale : LC_NUMERIC=C.UTF-8 contre la regression MoveIt 2 Kilted qui
serialise les doubles selon la locale (cf so101_moveit_config/demo.launch.py).
"""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import SetParameter


def generate_launch_description():
    bringup_share = get_package_share_directory('lekiwi_bringup')
    moveit_share = get_package_share_directory('lekiwi_manipulation_moveit_config')

    headless = LaunchConfiguration('headless')
    headless_arg = DeclareLaunchArgument(
        'headless', default_value='false',
        description='true = Gazebo serveur seul (sans GUI).')
    rviz = LaunchConfiguration('rviz')
    rviz_arg = DeclareLaunchArgument(
        'rviz', default_value='true', description='Lancer RViz MoveIt.')

    sim_full = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'sim_full.launch.py'])),
        launch_arguments={'headless': headless}.items(),
    )
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([moveit_share, 'launch', 'move_group.launch.py'])),
    )
    moveit_rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([moveit_share, 'launch', 'moveit_rviz.launch.py'])),
        condition=IfCondition(rviz),
    )

    return LaunchDescription([
        SetEnvironmentVariable('LC_NUMERIC', 'C.UTF-8'),
        SetParameter(name='use_sim_time', value=True),
        headless_arg,
        rviz_arg,
        sim_full,
        move_group,
        moveit_rviz,
    ])
