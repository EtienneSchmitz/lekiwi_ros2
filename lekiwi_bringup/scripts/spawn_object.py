#!/usr/bin/env python3
"""Spawn / supprime des objets a saisir dans le monde Gazebo Ionic (gz-sim 9).

Projet final (Jour 5) : depose des objets sur la STATION de prelevement du monde
warehouse.sdf, ou l'etudiant choisit le type d'objet et la pose. Mecanisme 100 %
Gazebo Ionic : services ros_gz_interfaces/srv/SpawnEntity (creation) et DeleteEntity
(suppression), pontes vers les services gz /world/<world>/create et /remove
(cf. config/bridge_spawn.yaml). PAS de spawn_entity.py (Gazebo Classic).

Exemples (le pont de services doit tourner, cf. spawn_object.launch.py) :
    ros2 run lekiwi_bringup spawn_object.py --ros-args -p object_type:=cube_color -p color:=green
    ros2 run lekiwi_bringup spawn_object.py --ros-args -p object_type:=cube_aruco -p aruco_id:=1
    ros2 run lekiwi_bringup spawn_object.py --ros-args -p object_type:=waste_can
    ros2 run lekiwi_bringup spawn_object.py --ros-args -p object_type:=sdf -p model_path:=/chemin/model.sdf
    ros2 run lekiwi_bringup spawn_object.py --ros-args -p action:=respawn -p name:=pick_object_0
    ros2 run lekiwi_bringup spawn_object.py --ros-args -p action:=delete -p name:=pick_object_0

Tout est parametrable : object_type, couleur / class_id / aruco_id, pose (ou pose
aleatoire dans la zone station), count, name, action (spawn|delete|respawn).
"""

import math
import os
import random

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Pose
from ros_gz_interfaces.msg import Entity, EntityFactory
from ros_gz_interfaces.srv import DeleteEntity, SpawnEntity

# Couleurs nommees -> rgba (sert aussi de classe pour la detection couleur).
COLORS = {
    'red':   (0.8, 0.1, 0.1, 1.0),
    'green': (0.1, 0.7, 0.2, 1.0),
    'blue':  (0.1, 0.3, 0.8, 1.0),
    'yellow': (0.85, 0.8, 0.1, 1.0),
}

WASTE_TYPES = ('waste_can', 'waste_bottle', 'waste_carton')


def yaw_to_quat(yaw):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


def cube_color_sdf(rgba):
    """SDF inline d'un cube 4 cm colore (couleur injectee)."""
    r, g, b, a = rgba
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <model name="pick_cube">
    <link name="link">
      <inertial><mass>0.02</mass>
        <inertia><ixx>5.33e-6</ixx><iyy>5.33e-6</iyy><izz>5.33e-6</izz>
          <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <collision name="collision"><geometry><box><size>0.04 0.04 0.04</size></box></geometry></collision>
      <visual name="visual"><geometry><box><size>0.04 0.04 0.04</size></box></geometry>
        <material><ambient>{r} {g} {b} {a}</ambient><diffuse>{r} {g} {b} {a}</diffuse>
          <specular>0.2 0.2 0.2 1</specular></material></visual>
    </link>
  </model>
</sdf>"""


def cube_aruco_sdf(marker_id):
    """SDF inline d'un cube 4 cm avec marqueur ArUco <id> sur le dessus.

    La texture est referencee par son CHEMIN ABSOLU : un SDF inline (spawne via
    le service create) n'a pas de dossier de reference, donc une URI relative
    n'est resolue que si le SERVEUR gz a .../models sur GZ_SIM_RESOURCE_PATH —
    ce qui n'est pas garanti. Le chemin absolu rend le SDF auto-suffisant.
    """
    from ament_index_python.packages import get_package_share_directory
    share = get_package_share_directory('lekiwi_bringup')
    tex = os.path.join(share, 'models', 'aruco_cube', 'materials',
                       'textures', f'aruco_{marker_id}.png')
    if not os.path.isfile(tex):
        # On garde le spawn (cube blanc) mais on previent : marqueur introuvable.
        import sys
        print(f"[spawn_object] ATTENTION: texture ArUco absente: {tex} "
              f"(generer avec: ros2 run lekiwi_bringup generate_aruco.py --id {marker_id})",
              file=sys.stderr)
    return f"""<?xml version="1.0"?>
<sdf version="1.9">
  <model name="aruco_cube">
    <link name="link">
      <inertial><mass>0.02</mass>
        <inertia><ixx>5.33e-6</ixx><iyy>5.33e-6</iyy><izz>5.33e-6</izz>
          <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz></inertia></inertial>
      <collision name="collision"><geometry><box><size>0.04 0.04 0.04</size></box></geometry></collision>
      <visual name="body"><geometry><box><size>0.04 0.04 0.04</size></box></geometry>
        <material><ambient>0.9 0.9 0.9 1</ambient><diffuse>0.95 0.95 0.95 1</diffuse></material></visual>
      <visual name="marker"><pose>0 0 0.0205 0 0 0</pose>
        <geometry><box><size>0.038 0.038 0.001</size></box></geometry>
        <material><ambient>1 1 1 1</ambient><diffuse>1 1 1 1</diffuse>
          <pbr><metal><albedo_map>{tex}</albedo_map>
            <metalness>0.0</metalness><roughness>1.0</roughness></metal></pbr></material></visual>
    </link>
  </model>
</sdf>"""


class ObjectSpawner(Node):
    def __init__(self):
        super().__init__('object_spawner')
        # --- Parametres ---
        self.declare_parameter('world', 'warehouse')
        self.declare_parameter('object_type', 'cube_color')      # cube_color|cube_aruco|waste_*|sdf
        self.declare_parameter('color', 'red')
        self.declare_parameter('class_id', '')                   # defaut : derive du type/couleur
        self.declare_parameter('aruco_id', 0)
        self.declare_parameter('model_path', '')                 # si object_type=sdf
        self.declare_parameter('pose', '')                       # "x y z [yaw]" ; vide => aleatoire
        self.declare_parameter('station_xy', [0.0, 4.6])         # centre zone station (= <pose> du monde)
        self.declare_parameter('station_z', 0.17)                # hauteur d'apparition (monde)
        self.declare_parameter('jitter', 0.06)                   # demi-cote de la zone aleatoire (m)
        self.declare_parameter('count', 1)
        self.declare_parameter('name', '')                       # vide => auto (pick_object_<i>)
        self.declare_parameter('action', 'spawn')               # spawn|delete|respawn
        self.declare_parameter('timeout', 10.0)

        self.world = self.get_parameter('world').value
        self.create_cli = self.create_client(SpawnEntity, f'/world/{self.world}/create')
        self.remove_cli = self.create_client(DeleteEntity, f'/world/{self.world}/remove')

    # ------------------------------------------------------------------ SDF
    def build_sdf(self):
        """Retourne (sdf_string, default_class_id) selon object_type."""
        otype = self.get_parameter('object_type').value
        if otype == 'cube_color':
            color = self.get_parameter('color').value
            rgba = self._resolve_color(color)
            return cube_color_sdf(rgba), str(color)
        if otype == 'cube_aruco':
            mid = int(self.get_parameter('aruco_id').value)
            return cube_aruco_sdf(mid), str(mid)
        if otype in WASTE_TYPES:
            return self._read_model_sdf(otype), {'waste_can': 'metal',
                                                 'waste_bottle': 'plastic',
                                                 'waste_carton': 'paper'}[otype]
        if otype == 'sdf':
            path = self.get_parameter('model_path').value
            if not path or not os.path.isfile(path):
                self.get_logger().error(f"model_path introuvable : '{path}'")
                return None, ''
            with open(path, 'r') as f:
                return f.read(), os.path.splitext(os.path.basename(path))[0]
        self.get_logger().error(f"object_type inconnu : '{otype}'")
        return None, ''

    def _resolve_color(self, color):
        if isinstance(color, str) and color in COLORS:
            return COLORS[color]
        # accepte "r g b a" (ou "r g b")
        try:
            parts = [float(v) for v in str(color).split()]
            if len(parts) == 3:
                parts.append(1.0)
            if len(parts) == 4:
                return tuple(parts)
        except ValueError:
            pass
        self.get_logger().warn(f"couleur '{color}' inconnue, rouge par defaut.")
        return COLORS['red']

    def _read_model_sdf(self, model_name):
        from ament_index_python.packages import get_package_share_directory
        share = get_package_share_directory('lekiwi_bringup')
        path = os.path.join(share, 'models', model_name, 'model.sdf')
        with open(path, 'r') as f:
            return f.read()

    # ----------------------------------------------------------------- pose
    def make_pose(self, index):
        pose_str = str(self.get_parameter('pose').value).strip()
        raw = [float(v) for v in pose_str.split()] if pose_str else []
        if len(raw) >= 3:  # pose explicite "x y z [yaw]"
            x, y, z = raw[0], raw[1], raw[2]
            yaw = raw[3] if len(raw) > 3 else 0.0
            if index:  # decaler les copies suivantes
                x += 0.06 * index
        else:     # pose aleatoire dans la zone station
            cx, cy = [float(v) for v in self.get_parameter('station_xy').value]
            j = float(self.get_parameter('jitter').value)
            x = cx + random.uniform(-j, j)
            y = cy + random.uniform(-j, j)
            z = float(self.get_parameter('station_z').value)
            yaw = random.uniform(-math.pi, math.pi)
        p = Pose()
        p.position.x, p.position.y, p.position.z = x, y, z
        qx, qy, qz, qw = yaw_to_quat(yaw)
        p.orientation.z, p.orientation.w = qz, qw
        return p

    # -------------------------------------------------------------- services
    def _wait(self, client, label):
        t = float(self.get_parameter('timeout').value)
        if not client.wait_for_service(timeout_sec=t):
            self.get_logger().error(
                f"service {label} indisponible (le pont de services tourne-t-il ? "
                f"cf. spawn_object.launch.py)")
            return False
        return True

    def spawn_one(self, name, sdf, pose):
        if not self._wait(self.create_cli, f'/world/{self.world}/create'):
            return False
        req = SpawnEntity.Request()
        ef = EntityFactory()
        ef.name = name
        ef.allow_renaming = False
        ef.sdf = sdf
        ef.pose = pose
        req.entity_factory = ef
        fut = self.create_cli.call_async(req)
        rclpy.spin_until_future_complete(self, fut, timeout_sec=15.0)
        ok = fut.result() is not None and fut.result().success
        self.get_logger().info(
            f"spawn '{name}' @ ({pose.position.x:.2f},{pose.position.y:.2f},"
            f"{pose.position.z:.2f}) -> {'OK' if ok else 'ECHEC'}")
        return ok

    def delete_one(self, name):
        if not self._wait(self.remove_cli, f'/world/{self.world}/remove'):
            return False
        req = DeleteEntity.Request()
        ent = Entity()
        ent.name = name
        ent.type = Entity.MODEL
        req.entity = ent
        fut = self.remove_cli.call_async(req)
        rclpy.spin_until_future_complete(self, fut, timeout_sec=15.0)
        ok = fut.result() is not None and fut.result().success
        self.get_logger().info(f"delete '{name}' -> {'OK' if ok else 'ECHEC (absent ?)'}")
        return ok

    # ------------------------------------------------------------------- run
    def names(self):
        base = self.get_parameter('name').value or 'pick_object'
        n = int(self.get_parameter('count').value)
        if self.get_parameter('name').value and n == 1:
            return [base]
        return [f'{base}_{i}' for i in range(n)]

    def run(self):
        action = self.get_parameter('action').value
        names = self.names()

        if action in ('delete', 'respawn'):
            for nm in names:
                self.delete_one(nm)
            if action == 'delete':
                return True

        sdf, default_class = self.build_sdf()
        if sdf is None:
            return False
        class_id = self.get_parameter('class_id').value or default_class
        self.get_logger().info(
            f"object_type='{self.get_parameter('object_type').value}' class_id='{class_id}' "
            f"x{len(names)}")
        ok = True
        for i, nm in enumerate(names):
            ok = self.spawn_one(nm, sdf, self.make_pose(i)) and ok
        return ok


def main():
    rclpy.init()
    node = ObjectSpawner()
    try:
        ok = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0 if ok else 1


if __name__ == '__main__':
    main()
