from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("lekiwi_manip", package_name="lekiwi_manipulation_moveit_config")
        # mode 'moveit' : URDF sans ros2_control ni plugin Gazebo.
        # cameras desactivees dans le modele de planification.
        .robot_description(mappings={
            "mode": "moveit",
            "wrist_camera": "false",
            "scene_camera": "false",
        })
        .to_moveit_configs()
    )
    return generate_move_group_launch(moveit_config)
