"""Simulation Gazebo (Ionic) de la PLATEFORME de manipulation mobile.

LeKiwi (base omni) + SO-101 (bras 6 DoF, prefixe arm_) + cameras RGB-D, dans une
seule robot_description avec un seul controller_manager.

Lance : Gazebo + spawn + ros_gz bridge (/clock, /scan, /imu, cameras)
        + robot_state_publisher + 4 controleurs + twist_mux + EKF.

Controleurs : joint_state_broadcaster, omni_wheel_drive_controller (base),
              arm_controller (bras), gripper_controller (pince).

Pilotage base (autre terminal) :
    ros2 run teleop_twist_keyboard --ros-args \
        -r /cmd_vel:=/cmd_vel_teleop -p stamped:=true

Cameras activables :
    ros2 launch lekiwi_bringup sim_full.launch.py wrist_camera:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument,
                            IncludeLaunchDescription, RegisterEventHandler)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    desc_share = get_package_share_directory('lekiwi_description')
    bringup_share = get_package_share_directory('lekiwi_bringup')
    so101_share = get_package_share_directory('so101_description')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    controllers_file = os.path.join(bringup_share, 'config', 'ros2_controllers.full.yaml')
    twist_mux_file = os.path.join(bringup_share, 'config', 'twist_mux.yaml')
    bridge_file = os.path.join(bringup_share, 'config', 'bridge_full.yaml')
    ekf_file = os.path.join(bringup_share, 'config', 'ekf.yaml')
    arm_init_file = os.path.join(bringup_share, 'config', 'arm_initial_positions.yaml')
    default_world = os.path.join(bringup_share, 'worlds', 'bootcamp.sdf')
    model_xacro = os.path.join(desc_share, 'urdf', 'lekiwi_manip.urdf.xacro')

    world_arg = DeclareLaunchArgument(
        'world', default_value=default_world, description='Monde SDF a charger.')
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true', description='Utiliser l horloge sim.')
    headless = LaunchConfiguration('headless')
    headless_arg = DeclareLaunchArgument(
        'headless', default_value='false',
        description='true = Gazebo serveur seul (sans GUI).')
    wrist_camera = LaunchConfiguration('wrist_camera')
    wrist_camera_arg = DeclareLaunchArgument(
        'wrist_camera', default_value='true',
        description='Ajouter la camera RGB-D du poignet (eye-in-hand).')
    scene_camera = LaunchConfiguration('scene_camera')
    scene_camera_arg = DeclareLaunchArgument(
        'scene_camera', default_value='true',
        description='Ajouter la camera RGB-D de scene (mat fixe).')

    # Resolution des meshes package://... pour les DEUX robots.
    set_resource_path_lekiwi = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.path.dirname(desc_share))
    set_resource_path_so101 = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.path.dirname(so101_share))

    # --- robot_description (plateforme, mode gazebo) ---
    robot_description = ParameterValue(
        Command([
            FindExecutable(name='xacro'), ' ', model_xacro,
            ' mode:=gazebo',
            ' controllers_file:=', controllers_file,
            ' arm_initial_positions_file:=', arm_init_file,
            ' wrist_camera:=', wrist_camera,
            ' scene_camera:=', scene_camera,
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
    gz_sim_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': [LaunchConfiguration('world'), ' -r -v4']}.items(),
        condition=UnlessCondition(headless),
    )
    gz_sim_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': [LaunchConfiguration('world'), ' -r -s -v4']}.items(),
        condition=IfCondition(headless),
    )

    spawn_robot = Node(
        package='ros_gz_sim', executable='create',
        arguments=['-topic', 'robot_description', '-name', 'lekiwi_manip', '-z', '0.1'],
        output='screen',
    )

    # --- Pont ros_gz (/clock, /scan, /imu, cameras) ---
    bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge',
        parameters=[{'config_file': bridge_file, 'use_sim_time': use_sim_time}],
        output='screen',
    )

    # --- Controleurs ros2_control ---
    jsb_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['joint_state_broadcaster',
                   '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', '60'],
    )
    omni_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=[
            'omni_wheel_drive_controller',
            '--controller-manager', '/controller_manager',
            '--controller-manager-timeout', '60',
            '--controller-ros-args', '-r /omni_wheel_drive_controller/cmd_vel:=/cmd_vel',
            '--controller-ros-args', '-r /omni_wheel_drive_controller/odom:=/odom',
        ],
    )
    arm_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['arm_controller',
                   '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', '60'],
    )
    gripper_spawner = Node(
        package='controller_manager', executable='spawner',
        arguments=['gripper_controller',
                   '--controller-manager', '/controller_manager',
                   '--controller-manager-timeout', '60'],
    )

    # --- twist_mux : sources -> /cmd_vel ---
    twist_mux = Node(
        package='twist_mux', executable='twist_mux',
        parameters=[twist_mux_file, {'use_sim_time': use_sim_time}],
        remappings=[('cmd_vel_out', '/cmd_vel')],
        output='screen',
    )

    # --- EKF : odom roues (/odom) + IMU (/imu/data) -> tf odom->base_footprint ---
    ekf = Node(
        package='robot_localization', executable='ekf_node', name='ekf_filter_node',
        parameters=[ekf_file, {'use_sim_time': use_sim_time}],
        output='screen',
    )

    # Ordonnancement : spawn -> jsb -> (omni + arm + gripper)
    after_spawn_jsb = RegisterEventHandler(
        OnProcessExit(target_action=spawn_robot, on_exit=[jsb_spawner]))
    after_jsb_controllers = RegisterEventHandler(
        OnProcessExit(target_action=jsb_spawner,
                      on_exit=[omni_spawner, arm_spawner, gripper_spawner]))

    return LaunchDescription([
        world_arg,
        use_sim_time_arg,
        headless_arg,
        wrist_camera_arg,
        scene_camera_arg,
        set_resource_path_lekiwi,
        set_resource_path_so101,
        robot_state_publisher,
        gz_sim_gui,
        gz_sim_headless,
        spawn_robot,
        bridge,
        after_spawn_jsb,
        after_jsb_controllers,
        twist_mux,
        ekf,
    ])
