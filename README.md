# lekiwi_ros2

Packages ROS 2 (Kilted) pour la base mobile **LeKiwi** — 3 roues omnidirectionnelles
(kiwi 120°) + LiDAR 360° **LDRobot D500** — utilisée au Bootcamp Robotique Perpignan 2026,
Jour 2 (Navigation). La **plateforme de manipulation mobile** (LeKiwi + bras SO-101 monté
+ caméras RGB-D) est ajoutée en Session S20, via le `mount_link` du plateau.

Inspiré de [adityakamath/lekiwi_ros2](https://github.com/adityakamath/lekiwi_ros2).

## Packages

| Package | Rôle |
| --- | --- |
| `lekiwi_description` | URDF Xacro base 3 roues + LiDAR D500 + RViz. Plateforme combinée (`lekiwi_manip.urdf.xacro` : base + bras SO-101 préfixé `arm_` + 2 caméras RGB-D) |
| `lekiwi_bringup` | Sim Gazebo (Ionic) : base seule (`sim_base`) ou plateforme complète (`sim_full`) |
| `lekiwi_navigation` | SLAM (slam_toolbox) + Nav2 holonome |
| `lekiwi_manipulation_moveit_config` | Config MoveIt 2 de la plateforme (groupe `arm`, virtual joint planar `odom`→`base_footprint`) |
| `lekiwi_manipulation` | Démo mobile-manip (S20.3) : orchestration navigation → pick (sans perception) |

> Le bras SO-101 vient du dépôt `so_arm101_ros2` (package `so101_description`),
> réutilisé en macro xacro paramétrée (`so101_arm`, préfixe `arm_`).

## Quickstart

```bash
cd ~/ros2_bootcamp_ws
colcon build
source install/setup.bash

# Visualiser la base + LiDAR dans RViz
ros2 launch lekiwi_description display.launch.py

# Simulation Gazebo + téléop clavier
ros2 launch lekiwi_bringup sim_base.launch.py
ros2 run teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel_teleop

# SLAM + navigation autonome Nav2
ros2 launch lekiwi_navigation navigation.launch.py
```

## Plateforme de manipulation mobile (S20)

```bash
# Sim complète : base + bras SO-101 + 2 caméras RGB-D
ros2 launch lekiwi_bringup sim_full.launch.py
# Caméras désactivables individuellement :
ros2 launch lekiwi_bringup sim_full.launch.py wrist_camera:=false scene_camera:=false

# MoveIt 2 sur la plateforme (sim + move_group + RViz)
ros2 launch lekiwi_manipulation_moveit_config demo_moveit.launch.py

# Démo end-to-end : navigation → pick (sans perception)
ros2 launch lekiwi_manipulation nav_pick_demo.launch.py
```

Topics caméras : `/wrist_camera/{image,depth_image,points,camera_info}` (poignet,
eye-in-hand) et `/scene_camera/...` (mât fixe). Prépare le Jour 4 (Vision) et le
Jour 5 (Intégration).

## Licence

MIT — voir [LICENSE](LICENSE).
