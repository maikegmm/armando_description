#!/usr/bin/env python3

import select
import sys
import termios
import tty

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


class ArmandoKeyboardTeleop(Node):
    def __init__(self):
        super().__init__('armando_keyboard_teleop')
        self.declare_parameter('step_size', 0.1)
        self.declare_parameter('move_duration_sec', 0.2)
        self.step_size = float(self.get_parameter('step_size').value)
        self.move_duration_sec = float(self.get_parameter('move_duration_sec').value)
        self.joint_names = ['j0', 'j1', 'j2', 'j3']
        self.joint_limits = {joint: (-3.14, 3.14) for joint in self.joint_names}
        self.positions = {joint: 0.0 for joint in self.joint_names}
        self.have_joint_state = False

        self.state_subscription = self.create_subscription(
            JointState, '/joint_states', self._update_joint_state, 10
        )
        self.trajectory_publisher = self.create_publisher(
            JointTrajectory,
            '/joint_trajectory_controller/joint_trajectory',
            10,
        )

    def _update_joint_state(self, message):
        state = dict(zip(message.name, message.position))
        if all(joint in state for joint in self.joint_names):
            self.positions.update({joint: state[joint] for joint in self.joint_names})
            self.have_joint_state = True

    def move_joint(self, joint, direction):
        lower, upper = self.joint_limits[joint]
        self.positions[joint] = min(
            upper,
            max(lower, self.positions[joint] + direction * self.step_size),
        )

        trajectory = JointTrajectory()
        trajectory.joint_names = self.joint_names
        point = JointTrajectoryPoint()
        point.positions = [self.positions[name] for name in self.joint_names]
        whole_seconds = int(self.move_duration_sec)
        point.time_from_start.sec = whole_seconds
        point.time_from_start.nanosec = int(
            (self.move_duration_sec - whole_seconds) * 1_000_000_000
        )
        trajectory.points = [point]
        self.trajectory_publisher.publish(trajectory)
        self.get_logger().info(f'{joint}: {self.positions[joint]:+.3f} rad')


def main(args=None):
    rclpy.init(args=args)
    node = ArmandoKeyboardTeleop()
    terminal_settings = None

    try:
        if not sys.stdin.isatty():
            node.get_logger().error('Avvia il nodo da un terminale interattivo.')
            return 1

        node.get_logger().info('In attesa di /joint_states (massimo 5 secondi)...')
        for _ in range(50):
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.have_joint_state:
                break
        if not node.have_joint_state:
            node.get_logger().error(
                'Stati dei quattro giunti non ricevuti. '
                'Avvia la simulazione e il joint_state_broadcaster.'
            )
            return 1

        key_bindings = {
            'q': ('j0', 1), 'a': ('j0', -1),
            'w': ('j1', 1), 's': ('j1', -1),
            'e': ('j2', 1), 'd': ('j2', -1),
            'r': ('j3', 1), 'f': ('j3', -1),
        }
        print('q/a: j0 | w/s: j1 | e/d: j2 | r/f: j3 | Esc: esci')
        terminal_settings = termios.tcgetattr(sys.stdin.fileno())
        tty.setraw(sys.stdin.fileno())

        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.0)
            readable, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not readable:
                continue
            key = sys.stdin.read(1)
            if key == '\x1b':
                break
            if key in key_bindings:
                joint, direction = key_bindings[key]
                node.move_joint(joint, direction)
    except KeyboardInterrupt:
        pass
    finally:
        if terminal_settings is not None:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, terminal_settings)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    return 0


if __name__ == '__main__':
    sys.exit(main())
