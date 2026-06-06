# Origine des meshes

Meshes de la base LeKiwi vendorisées depuis
[adityakamath/lekiwi_ros2](https://github.com/adityakamath/lekiwi_ros2)
(`lekiwi_description/meshes/base/`), sous licence **Apache-2.0**.

| Fichier | Rôle |
| --- | --- |
| `lekiwi_base.stl` | plateau de la base |
| `omni_wheel.stl` | roue omnidirectionnelle (galets), ×3 |
| `ld06_lidar.stl` | LiDAR LDRobot (représente le D500, même famille) |
| `bno055_imu.stl` | IMU BNO055 |

Ces STL ont été **décimés** (clustering de sommets) pour alléger le repo et la
simulation, sans changer les dimensions (bounding box préservée) :
`lekiwi_base` 851k→27k tris, `omni_wheel` 543k→40k tris, `bno055_imu` 34k→1.4k tris.
