# lekiwi_ros2

Packages ROS 2 (Kilted) pour la base mobile **LeKiwi** — 3 roues omnidirectionnelles
(kiwi 120°) + LiDAR 360° **LDRobot D500** — utilisée au Bootcamp Robotique Perpignan 2026,
Jour 2 (Navigation). La plateforme complète (LeKiwi + bras SO-101 monté) sera ajoutée en
Session S20 via le `mount_link` déjà prévu dans l'URDF.

Inspiré de [adityakamath/lekiwi_ros2](https://github.com/adityakamath/lekiwi_ros2).

## Packages

| Package | Rôle |
| --- | --- |
| `lekiwi_description` | URDF Xacro base 3 roues + LiDAR D500 + RViz |
| `lekiwi_bringup` | Sim Gazebo (Ionic) + ros2_control (omni_wheel_drive_controller) |
| `lekiwi_navigation` | SLAM (slam_toolbox) + Nav2 holonome |

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

## Licence

MIT — voir [LICENSE](LICENSE).
