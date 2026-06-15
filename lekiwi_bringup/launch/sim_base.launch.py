"""Simulation Gazebo (Ionic) de la base LeKiwi seule.

Lance : Gazebo + spawn du robot + ros_gz bridge (/clock, /scan)
        + robot_state_publisher + controleurs ros2_control + twist_mux.

Pilotage (dans un autre terminal) :
    ros2 run teleop_twist_keyboard --ros-args \
        -r /cmd_vel:=/cmd_vel_teleop -p stamped:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, OpaqueFunction,
                            RegisterEventHandler)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    desc_share = get_package_share_directory('lekiwi_description')
    bringup_share = get_package_share_directory('lekiwi_bringup')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    controllers_file = os.path.join(bringup_share, 'config', 'ros2_controllers.yaml')
    twist_mux_file = os.path.join(bringup_share, 'config', 'twist_mux.yaml')
    bridge_file = os.path.join(bringup_share, 'config', 'bridge.yaml')
    ekf_file = os.path.join(bringup_share, 'config', 'ekf.yaml')
    model_xacro = os.path.join(desc_share, 'urdf', 'lekiwi.urdf.xacro')

    world_arg = DeclareLaunchArgument(
        'world', default_value='bootcamp',
        description="Monde a charger : nom court (ex: warehouse, bootcamp) "
                    "resolu dans worlds/, ou chemin .sdf complet.")
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true', description='Utiliser l horloge sim.')
    headless = LaunchConfiguration('headless')
    headless_arg = DeclareLaunchArgument(
        'headless', default_value='false',
        description='true = Gazebo serveur seul (sans GUI).')

    # Permet a Gazebo de resoudre les meshes package://lekiwi_description/...
    # (sinon le robot spawn sans visuel : seules les collisions existent).
    set_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.path.dirname(desc_share))

    # --- robot_description (mode gazebo, avec le fichier de controleurs) ---
    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ', model_xacro,
            ' mode:=gazebo',
            ' controllers_file:=', controllers_file,
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': use_sim_time}],
    )

    # --- Gazebo (GUI ou serveur seul selon 'headless') ---
    # Resolution differee du monde (nom court -> chemin) via OpaqueFunction :
    # 'warehouse' -> worlds/warehouse.sdf ; un chemin absolu est utilise tel quel.
    def gz_sim_setup(context):
        world = LaunchConfiguration('world').perform(context)
        if world and not os.path.isabs(world):
            name = world if world.endswith('.sdf') else f'{world}.sdf'
            world = os.path.join(bringup_share, 'worlds', name)
        gz_launch = PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py'))
        return [
            IncludeLaunchDescription(
                gz_launch,
                launch_arguments={'gz_args': f'{world} -r -v4'}.items(),
                condition=UnlessCondition(headless),
            ),
            IncludeLaunchDescription(
                gz_launch,
                launch_arguments={'gz_args': f'{world} -r -s -v4'}.items(),
                condition=IfCondition(headless),
            ),
        ]

    gz_sim = OpaqueFunction(function=gz_sim_setup)

    spawn_robot = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'lekiwi', '-z', '0.1'],
        output='screen',
    )

    # --- Pont ros_gz (/clock, /scan) ---
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        parameters=[{'config_file': bridge_file, 'use_sim_time': use_sim_time}],
        output='screen',
    )

    # --- Controleurs ros2_control ---
    jsb_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster'],
    )
    omni_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=[
            'omni_wheel_drive_controller',
            '--controller-ros-args', '-r /omni_wheel_drive_controller/cmd_vel:=/cmd_vel',
            '--controller-ros-args', '-r /omni_wheel_drive_controller/odom:=/odom',
        ],
    )

    # --- twist_mux : sources -> /cmd_vel ---
    twist_mux = Node(
        package='twist_mux', executable='twist_mux',
        parameters=[twist_mux_file, {'use_sim_time': use_sim_time}],
        remappings=[('cmd_vel_out', '/cmd_vel')],
        output='screen',
    )

    # --- EKF : fusion odom roues (/odom) + IMU (/imu/data) -> tf odom->base_footprint ---
    ekf = Node(
        package='robot_localization', executable='ekf_node', name='ekf_filter_node',
        parameters=[ekf_file, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Ordonnancement : spawn -> jsb -> omni
    after_spawn_jsb = RegisterEventHandler(
        OnProcessExit(target_action=spawn_robot, on_exit=[jsb_spawner]))
    after_jsb_omni = RegisterEventHandler(
        OnProcessExit(target_action=jsb_spawner, on_exit=[omni_spawner]))

    return LaunchDescription([
        world_arg,
        use_sim_time_arg,
        headless_arg,
        set_resource_path,
        robot_state_publisher,
        gz_sim,
        spawn_robot,
        bridge,
        after_spawn_jsb,
        after_jsb_omni,
        twist_mux,
        ekf,
    ])
