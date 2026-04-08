#!/usr/bin/env python3
"""
三舵轮 Gazebo Classic 仿真启动：
  source /opt/ros/humble/setup.bash && colcon build --packages-select three_steer_simulation
  source install/setup.bash
  ros2 launch three_steer_simulation three_steer_gazebo.launch.py

键盘（默认 keyboard:=true，需在运行 launch 的终端内按键；全向平移请按住 Shift 再用 U/I/O 等）：
  i/,  前后    j/l  自转    u/o/m/.  斜向    Shift+IJLK  左右平移

关闭内置键盘：  ros2 launch ... three_steer_gazebo.launch.py keyboard:=false
（仍可自行向 /cmd_vel 发速度，由 cmd_vel_to_three_steer 转换）
"""
import os
import subprocess
import tempfile
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler, OpaqueFunction
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('three_steer_simulation')
    xacro_file = os.path.join(pkg_share, 'urdf', 'three_steer.urdf.xacro')
    controllers = os.path.join(pkg_share, 'config', 'controllers.yaml')
    fd, urdf_path = tempfile.mkstemp(suffix='.urdf')
    os.close(fd)
    subprocess.run(
        ['xacro', xacro_file, f'controllers_file:={controllers}', '-o', urdf_path],
        check=True,
    )
    with open(urdf_path, encoding='utf-8') as f:
        robot_description = f.read()

    from launch_ros.actions import Node

    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        output='screen',
    )

    # 在世界系原点水平放置：显式 x/y/yaw=0，避免依赖默认值；reference_frame 与 SpawnEntity.srv 约定一致
    spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-file', urdf_path,
            '-entity', 'three_steer_robot',
            '-reference_frame', 'world',
            '-x', '0',
            '-y', '0',
            '-z', '0.18',
            '-R', '0',
            '-P', '0',
            '-Y', '0',
        ],
        output='screen',
    )

    load_jsb = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '-c', '/controller_manager'],
        output='screen',
    )

    load_steer = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['steer_group_controller', '-c', '/controller_manager'],
        output='screen',
    )

    load_wheel = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['wheel_group_controller', '-c', '/controller_manager'],
        output='screen',
    )

    delay_jsb = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=spawn, on_exit=[load_jsb]),
    )
    delay_steer = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=load_jsb, on_exit=[load_steer]),
    )
    delay_wheel = RegisterEventHandler(
        event_handler=OnProcessExit(target_action=load_steer, on_exit=[load_wheel]),
    )

    bridge = Node(
        package='three_steer_simulation',
        executable='cmd_vel_to_three_steer.py',
        name='cmd_vel_to_three_steer',
        parameters=[{'use_sim_time': True, 'invert_wheel_sign': -1.0}],
        output='screen',
    )

    teleop = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        parameters=[{'speed': 0.65, 'turn': 1.2}],
        output='screen',
    )

    keyboard_on = LaunchConfiguration('keyboard').perform(context).lower() in ('true', '1', 'yes')
    delay_teleop = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=load_wheel,
            on_exit=[bridge] + ([teleop] if keyboard_on else []),
        ),
    )

    return [rsp, spawn, delay_jsb, delay_steer, delay_wheel, delay_teleop]


def generate_launch_description():
    world_file = os.path.join(
        get_package_share_directory('three_steer_simulation'),
        'worlds',
        'three_steer.world',
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('gazebo_ros'),
                'launch',
                'gazebo.launch.py',
            )
        ),
        launch_arguments={
            'verbose': 'false',
            'world': world_file,
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'keyboard',
            default_value='true',
            description='若为 true，在控制器就绪后启动 teleop_twist_keyboard（需在启动仿真的同一终端按键）',
        ),
        gazebo,
        OpaqueFunction(function=launch_setup),
    ])
