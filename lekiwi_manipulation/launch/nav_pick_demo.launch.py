"""Demo mobile-manip end-to-end (S20.3) : sim + Nav2 + MoveIt + orchestrateur.

Empile :
  - lekiwi_bringup/sim_full.launch.py            (plateforme : base + bras + cameras)
  - lekiwi_navigation/slam.launch.py             (slam_toolbox, map->odom)
  - lekiwi_navigation/nav2.launch.py             (Nav2)
  - lekiwi_manipulation_moveit_config/move_group (MoveIt, groupe arm)
  - nav_then_pick                                (navigation -> pick, sans perception)

NB : on inclut slam + nav2 directement (PAS navigation.launch.py, qui re-spawne
la base via sim_base). Une seule sim ros2_control (sim_full) est lancee.

    ros2 launch lekiwi_manipulation nav_pick_demo.launch.py headless:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription,
                            SetEnvironmentVariable, TimerAction)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, SetParameter


def generate_launch_description():
    bringup_share = get_package_share_directory('lekiwi_bringup')
    nav_share = get_package_share_directory('lekiwi_navigation')
    moveit_share = get_package_share_directory('lekiwi_manipulation_moveit_config')
    manip_share = get_package_share_directory('lekiwi_manipulation')

    pick_poses = os.path.join(manip_share, 'config', 'pick_poses.yaml')

    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('rviz')

    sim_full = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([bringup_share, 'launch', 'sim_full.launch.py'])),
        launch_arguments={'headless': headless}.items(),
    )
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav_share, 'launch', 'slam.launch.py'])),
        launch_arguments={'use_sim_time': 'true', 'slam_mode': 'map'}.items(),
    )
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([nav_share, 'launch', 'nav2.launch.py'])),
        launch_arguments={'use_sim_time': 'true'}.items(),
    )
    move_group = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([moveit_share, 'launch', 'move_group.launch.py'])),
    )
    moveit_rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([moveit_share, 'launch', 'moveit_rviz.launch.py'])),
        condition=IfCondition(use_rviz),
    )

    # Orchestrateur : demarre apres que sim/Nav2/MoveIt aient eu le temps de monter.
    nav_then_pick = Node(
        package='lekiwi_manipulation', executable='nav_then_pick',
        name='nav_then_pick', output='screen',
        parameters=[pick_poses, {'use_sim_time': True}],
    )
    delayed_orchestrator = TimerAction(period=25.0, actions=[nav_then_pick])

    return LaunchDescription([
        SetEnvironmentVariable('LC_NUMERIC', 'C.UTF-8'),
        SetParameter(name='use_sim_time', value=True),
        DeclareLaunchArgument('headless', default_value='false',
                              description='true = Gazebo sans GUI.'),
        DeclareLaunchArgument('rviz', default_value='false',
                              description='Lancer RViz MoveIt.'),
        sim_full,
        slam,
        nav2,
        move_group,
        moveit_rviz,
        delayed_orchestrator,
    ])
