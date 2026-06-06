"""Visualise la base LeKiwi (base + LiDAR) dans RViz.

Lance: robot_state_publisher + joint_state_publisher_gui + rviz2.
Mode 'display' : pas de ros2_control ni de plugin Gazebo.
"""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory('lekiwi_description')

    default_model = PathJoinSubstitution([pkg_share, 'urdf', 'lekiwi.urdf.xacro'])
    default_rviz = PathJoinSubstitution([pkg_share, 'rviz', 'lekiwi.rviz'])

    model_arg = DeclareLaunchArgument(
        'model', default_value=default_model,
        description='Chemin du Xacro LeKiwi a charger.'
    )
    rviz_arg = DeclareLaunchArgument(
        'rviz_config', default_value=default_rviz,
        description='Chemin du fichier de config RViz.'
    )

    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ',
            LaunchConfiguration('model'),
            ' mode:=display',
        ]),
        value_type=str,
    )

    return LaunchDescription([
        model_arg,
        rviz_arg,
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', LaunchConfiguration('rviz_config')],
        ),
    ])
