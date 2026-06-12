#!/usr/bin/env python3
"""Teleoperation clavier (AZERTY) de la base holonome LeKiwi.

Ce noeud lit les touches du clavier et publie des consignes de vitesse
geometry_msgs/TwistStamped sur le topic /cmd_vel_teleop. Le multiplexeur
twist_mux les arbitre avec les autres sources (Nav2) vers /cmd_vel, consomme
par omni_wheel_drive_controller. Aucun remap ni parametre supplementaire requis.

Commandes (disposition AZERTY) :

    z / s   translation longitudinale  (avancer / reculer)
    q / d   translation laterale       (gauche / droite, base holonome)
    a / e   rotation                   (gauche / droite)
    espace  arret
    + / -   ajuster la vitesse lineaire
    * / :   ajuster la vitesse angulaire
    x       quitter (ou Ctrl-C)

La derniere consigne est maintenue jusqu'a une nouvelle touche ou un arret.

Usage :
    ros2 run lekiwi_bringup teleop_azerty
"""

import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import TwistStamped
from rclpy.node import Node

# touche -> (dx, dy, dyaw) en unites normalisees (-1, 0, +1)
MOVE_BINDINGS = {
    'z': (1.0, 0.0, 0.0),    # avancer
    's': (-1.0, 0.0, 0.0),   # reculer
    'q': (0.0, 1.0, 0.0),    # strafe gauche (+y)
    'd': (0.0, -1.0, 0.0),   # strafe droite (-y)
    'a': (0.0, 0.0, 1.0),    # rotation gauche (+yaw)
    'e': (0.0, 0.0, -1.0),   # rotation droite (-yaw)
}
# touche -> (facteur vitesse lineaire, facteur vitesse angulaire)
SPEED_BINDINGS = {
    '+': (1.1, 1.0),
    '-': (0.9, 1.0),
    '*': (1.0, 1.1),
    ':': (1.0, 0.9),
}

HELP = __doc__


def get_key(settings):
    """Lit une touche (bloquant) en mode raw."""
    tty.setraw(sys.stdin.fileno())
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key


def main():
    rclpy.init()
    node = Node('teleop_azerty')
    pub = node.create_publisher(TwistStamped, '/cmd_vel_teleop', 10)

    lin_speed = 0.2   # m/s
    ang_speed = 0.8   # rad/s
    dx = dy = dyaw = 0.0

    settings = termios.tcgetattr(sys.stdin)
    print(HELP)
    print(f'\r\nvitesses : lineaire={lin_speed:.2f} m/s  angulaire={ang_speed:.2f} rad/s\r')

    try:
        while rclpy.ok():
            key = get_key(settings)
            if key in MOVE_BINDINGS:
                dx, dy, dyaw = MOVE_BINDINGS[key]
            elif key == ' ':
                dx = dy = dyaw = 0.0
            elif key in SPEED_BINDINGS:
                fl, fa = SPEED_BINDINGS[key]
                lin_speed *= fl
                ang_speed *= fa
                print(f'\rvitesses : lineaire={lin_speed:.2f} m/s  '
                      f'angulaire={ang_speed:.2f} rad/s        \r')
            elif key == 'x' or key == '\x03':  # x ou Ctrl-C
                break
            else:
                # touche inconnue : on stoppe (securite)
                dx = dy = dyaw = 0.0

            msg = TwistStamped()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.header.frame_id = 'base_link'
            msg.twist.linear.x = dx * lin_speed
            msg.twist.linear.y = dy * lin_speed
            msg.twist.angular.z = dyaw * ang_speed
            pub.publish(msg)
    except Exception as exc:  # noqa: BLE001
        print(f'\r\nteleop_azerty: {exc}\r')
    finally:
        # stop net avant de quitter
        stop = TwistStamped()
        stop.header.stamp = node.get_clock().now().to_msg()
        stop.header.frame_id = 'base_link'
        pub.publish(stop)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
