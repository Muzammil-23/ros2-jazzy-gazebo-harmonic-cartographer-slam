import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch_ros.actions import Node
from launch.substitutions import Command

def generate_launch_description():
    pkg_share = get_package_share_directory('concorde')
    xacro_file = os.path.join(pkg_share, 'urdf', 'concorde.xacro')
    lidar_sdf = os.path.join(pkg_share, 'config', 'lidar.sdf')
    world_sdf = os.path.join(pkg_share, 'config', 'concorde_world.sdf')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'robot_description': Command(['xacro ', xacro_file])},
            {'use_sim_time': True}
        ]
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        parameters=[{'use_sim_time': True}]
    )

    gazebo = ExecuteProcess(
        cmd=['gz', 'sim', '-r', world_sdf],
        output='screen'
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'concorde', '-topic', 'robot_description',
                   '-x', '0', '-y', '0', '-z', '0.05'],
        output='screen'
    )

    spawn_lidar = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'concorde_lidar', '-file', lidar_sdf,
                   '-x', '0', '-y', '0', '-z', '0.1'],
        output='screen'
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/model/concorde/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen'
    )

    static_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '0', '--z', '0',
                   '--roll', '0', '--pitch', '0', '--yaw', '0',
                   '--frame-id', 'odom', '--child-frame-id', 'base_link'],
    )

    static_laser = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '0', '--z', '0.05',
                   '--roll', '0', '--pitch', '0', '--yaw', '0',
                   '--frame-id', 'base_link', '--child-frame-id', 'laser_link'],
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher,
        bridge,
        static_odom,
        static_laser,
        gazebo,
        TimerAction(period=20.0, actions=[spawn_robot]),
        TimerAction(period=22.0, actions=[spawn_lidar]),
    ])