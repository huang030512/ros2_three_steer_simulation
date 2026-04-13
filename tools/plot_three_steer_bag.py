from pathlib import Path
import sys

import numpy as np
import matplotlib.pyplot as plt
from rosbags.highlevel import AnyReader
from rosbags.typesys import Stores, get_typestore

CMD_VEL = '/cmd_vel'
STEER_CMD = '/steer_group_controller/commands'
WHEEL_CMD = '/wheel_group_controller/commands'
JOINT_STATES = '/joint_states'

WHEEL_LABELS = ['front', 'left', 'right']


def to_sec_list(ts_list, t0):
    return [(t - t0) * 1e-9 for t in ts_list]


def save_cmd_vel_plot(bag_path, t0, cmd_times, cmd_vx, cmd_vy, cmd_wz):
    plt.figure(figsize=(10, 5))
    t = to_sec_list(cmd_times, t0)

    plt.plot(t, cmd_vx, label='vx [m/s]')
    plt.plot(t, cmd_vy, label='vy [m/s]')
    plt.plot(t, cmd_wz, label='wz [rad/s]')

    plt.title('Command Velocity')
    plt.xlabel('Time [s]')
    plt.ylabel('Velocity')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = bag_path / 'cmd_vel.png'
    plt.savefig(output, dpi=300)
    plt.close()
    print(f'Saved: {output}')


def save_steer_plot(bag_path, t0, steer_cmd_times, steer_cmd_vals):
    plt.figure(figsize=(10, 5))

    if steer_cmd_vals:
        steer_cmd_vals = np.array(steer_cmd_vals)
        t = to_sec_list(steer_cmd_times, t0)
        for i in range(min(3, steer_cmd_vals.shape[1])):
            plt.plot(t, steer_cmd_vals[:, i], label=f'{WHEEL_LABELS[i]} steer cmd')

    plt.title('Steer Command Angles')
    plt.xlabel('Time [s]')
    plt.ylabel('Angle [rad]')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = bag_path / 'steer_angles.png'
    plt.savefig(output, dpi=300)
    plt.close()
    print(f'Saved: {output}')


def save_wheel_plot(bag_path, t0, wheel_cmd_times, wheel_cmd_vals):
    plt.figure(figsize=(10, 5))

    if wheel_cmd_vals:
        wheel_cmd_vals = np.array(wheel_cmd_vals)
        t = to_sec_list(wheel_cmd_times, t0)
        for i in range(min(3, wheel_cmd_vals.shape[1])):
            plt.plot(t, wheel_cmd_vals[:, i], label=f'{WHEEL_LABELS[i]} wheel cmd')

    plt.title('Wheel Command Speeds')
    plt.xlabel('Time [s]')
    plt.ylabel('Angular Speed [rad/s]')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    output = bag_path / 'wheel_speeds.png'
    plt.savefig(output, dpi=300)
    plt.close()
    print(f'Saved: {output}')


def main():
    if len(sys.argv) < 2:
        print('Usage: python3 plot_three_steer_bag.py <bag_dir>')
        return

    bag_path = Path(sys.argv[1])
    typestore = get_typestore(Stores.ROS2_HUMBLE)

    cmd_times = []
    cmd_vx = []
    cmd_vy = []
    cmd_wz = []

    steer_cmd_times = []
    steer_cmd_vals = []

    wheel_cmd_times = []
    wheel_cmd_vals = []

    all_times = []

    with AnyReader([bag_path], default_typestore=typestore) as reader:
        for connection, timestamp, rawdata in reader.messages():
            topic = connection.topic
            msg = reader.deserialize(rawdata, connection.msgtype)
            all_times.append(timestamp)

            if topic == CMD_VEL:
                cmd_times.append(timestamp)
                cmd_vx.append(msg.linear.x)
                cmd_vy.append(msg.linear.y)
                cmd_wz.append(msg.angular.z)

            elif topic == STEER_CMD:
                steer_cmd_times.append(timestamp)
                steer_cmd_vals.append(list(msg.data))

            elif topic == WHEEL_CMD:
                wheel_cmd_times.append(timestamp)
                wheel_cmd_vals.append(list(msg.data))

    if not all_times:
        print('No messages found in bag.')
        return

    t0 = min(all_times)

    save_cmd_vel_plot(bag_path, t0, cmd_times, cmd_vx, cmd_vy, cmd_wz)
    save_steer_plot(bag_path, t0, steer_cmd_times, steer_cmd_vals)
    save_wheel_plot(bag_path, t0, wheel_cmd_times, wheel_cmd_vals)

    print(f'All figures saved under: {bag_path}')


if __name__ == '__main__':
    main()