#!/usr/bin/env python3
"""Demo de manipulation mobile (S20.3) : navigation -> pick, SANS perception.

Sequence :
  1. Attendre Nav2, envoyer un NavigateToPose vers une zone de travail pre-calculee.
  2. A l'arrivee, derouler une sequence de pick MoveIt (poses articulaires
     pre-calculees) : ready -> pince ouverte -> pre_pick -> pick -> pince fermee
     -> pre_pick -> ready.

Toutes les poses/le but sont des parametres (cf. config/pick_poses.yaml). C'est
le squelette du Jour 5 ou le 'detector' (Jour 4) fournira la pose reelle a la
place des valeurs pre-calculees.

Actions utilisees :
  navigate_to_pose                     (nav2_msgs/action/NavigateToPose)
  move_action                          (moveit_msgs/action/MoveGroup)
  /gripper_controller/gripper_cmd      (control_msgs/action/GripperCommand)
"""

import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from control_msgs.action import ParallelGripperCommand
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (Constraints, JointConstraint, MotionPlanRequest,
                             PlanningOptions)
from nav2_msgs.action import NavigateToPose

ARM_JOINTS = ['arm_shoulder_pan', 'arm_shoulder_lift', 'arm_elbow_flex',
              'arm_wrist_flex', 'arm_wrist_roll']
GRIPPER_JOINT = 'arm_gripper'


def yaw_to_quat(yaw):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


class NavThenPick(Node):
    def __init__(self):
        super().__init__('nav_then_pick')
        # Parametres (defauts alignes sur config/pick_poses.yaml)
        self.declare_parameter('nav_goal', [1.0, 0.0, 0.0])
        self.declare_parameter('pose_ready', [0.0, -1.0, 1.5, 0.0, 0.0])
        self.declare_parameter('pose_pre_pick', [0.0, -0.6, 1.2, 0.4, 0.0])
        self.declare_parameter('pose_pick', [0.0, -0.3, 0.9, 0.6, 0.0])
        self.declare_parameter('gripper_open', 1.5)
        self.declare_parameter('gripper_close', 0.0)
        self.declare_parameter('plan_time', 8.0)
        self.declare_parameter('frame_id', 'map')
        self.declare_parameter('skip_nav', False)

        self.plan_time = float(self.get_parameter('plan_time').value)
        self.nav_cli = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self.move_cli = ActionClient(self, MoveGroup, 'move_action')
        self.grip_cli = ActionClient(self, ParallelGripperCommand,
                                     '/gripper_controller/gripper_cmd')

    # ---------------------------------------------------------------- helpers
    def _send_and_wait(self, client, goal, label, timeout=120.0):
        self.get_logger().info(f'[{label}] envoi du goal...')
        if not client.wait_for_server(timeout_sec=30.0):
            self.get_logger().error(f'[{label}] serveur d action indisponible')
            return False
        send = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send, timeout_sec=30.0)
        gh = send.result()
        if gh is None or not gh.accepted:
            self.get_logger().error(f'[{label}] goal refuse')
            return False
        res = gh.get_result_async()
        rclpy.spin_until_future_complete(self, res, timeout_sec=timeout)
        if res.result() is None:
            self.get_logger().error(f'[{label}] timeout / pas de resultat')
            return False
        self.get_logger().info(f'[{label}] termine')
        return True

    def navigate(self):
        x, y, yaw = [float(v) for v in self.get_parameter('nav_goal').value]
        goal = NavigateToPose.Goal()
        ps = PoseStamped()
        ps.header.frame_id = self.get_parameter('frame_id').value
        ps.pose.position.x = x
        ps.pose.position.y = y
        qx, qy, qz, qw = yaw_to_quat(yaw)
        ps.pose.orientation.z = qz
        ps.pose.orientation.w = qw
        goal.pose = ps
        return self._send_and_wait(self.nav_cli, goal,
                                   f'NAV ({x:.2f},{y:.2f},{yaw:.2f})', timeout=180.0)

    def move_arm(self, joint_values, label):
        goal = MoveGroup.Goal()
        req = MotionPlanRequest()
        req.group_name = 'arm'
        req.num_planning_attempts = 10
        req.allowed_planning_time = self.plan_time
        req.max_velocity_scaling_factor = 0.2
        req.max_acceleration_scaling_factor = 0.2
        c = Constraints()
        for name, val in zip(ARM_JOINTS, joint_values):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = float(val)
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            c.joint_constraints.append(jc)
        req.goal_constraints.append(c)
        goal.request = req
        opts = PlanningOptions()
        opts.plan_only = False           # planifier ET executer
        goal.planning_options = opts
        return self._send_and_wait(self.move_cli, goal, f'ARM {label}')

    def gripper(self, position, label):
        goal = ParallelGripperCommand.Goal()
        goal.command.name = [GRIPPER_JOINT]
        goal.command.position = [float(position)]
        return self._send_and_wait(self.grip_cli, goal, f'GRIPPER {label}')

    # ------------------------------------------------------------------- run
    def run(self):
        ready = self.get_parameter('pose_ready').value
        pre = self.get_parameter('pose_pre_pick').value
        pick = self.get_parameter('pose_pick').value
        g_open = self.get_parameter('gripper_open').value
        g_close = self.get_parameter('gripper_close').value

        if not self.get_parameter('skip_nav').value:
            if not self.navigate():
                self.get_logger().error('Navigation echouee, abandon.')
                return False
        else:
            self.get_logger().info('skip_nav=true : on saute la navigation.')

        steps = [
            lambda: self.move_arm(ready, 'ready'),
            lambda: self.gripper(g_open, 'open'),
            lambda: self.move_arm(pre, 'pre_pick'),
            lambda: self.move_arm(pick, 'pick'),
            lambda: self.gripper(g_close, 'close'),
            lambda: self.move_arm(pre, 'retreat'),
            lambda: self.move_arm(ready, 'ready'),
        ]
        for step in steps:
            if not step():
                self.get_logger().error('Etape echouee, abandon de la sequence.')
                return False
        self.get_logger().info('Demo nav->pick terminee avec SUCCES.')
        return True


def main():
    rclpy.init()
    node = NavThenPick()
    try:
        ok = node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0 if ok else 1


if __name__ == '__main__':
    main()
