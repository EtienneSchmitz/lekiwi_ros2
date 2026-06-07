from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_moveit_rviz_launch


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("lekiwi_manip", package_name="lekiwi_manipulation_moveit_config")
        .robot_description(mappings={
            "mode": "moveit",
            "wrist_camera": "false",
            "scene_camera": "false",
        })
        .to_moveit_configs()
    )
    return generate_moveit_rviz_launch(moveit_config)
