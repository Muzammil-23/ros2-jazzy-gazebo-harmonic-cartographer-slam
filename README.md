# ros2-jazzy-gazebo-harmonic-cartographer-slam

ROS 2 Jazzy + Gazebo Harmonic differential drive robot with LiDAR-based SLAM mapping using Cartographer. Includes working world SDF, sensor bridge config, and Cartographer Lua — with documented fixes for Gazebo Harmonic sensor, plugin, and TF gotchas.

## Demo

| Gazebo Simulation | SLAM Map in RViz |
|---|---|
| ![Gazebo](images/gazebo.png) | ![Map](images/rviz.png) |

---
## Requirements

### System
| Requirement | Version |
|---|---|
| Ubuntu | 24.04 Noble |
| ROS 2 | Jazzy |
| Gazebo | Harmonic (gz-sim8) |
| Python | 3.12 |

### ROS 2 Packages
All required packages can be installed with:
```bash
sudo apt install -y \
  ros-jazzy-ros-gz \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-ros-gz-sim \
  ros-jazzy-cartographer-ros \
  ros-jazzy-nav2-map-server \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-tf2-ros \
  ros-jazzy-tf2-tools \
  ros-jazzy-teleop-twist-keyboard \
  ros-jazzy-xacro
```

### Environment Variables
Add these to your `~/.bashrc` — required for Gazebo transport to work correctly on single-machine setups:
```bash
export GZ_IP=127.0.0.1
export GZ_PARTITION=concorde
export ROS_DOMAIN_ID=0
```

---
