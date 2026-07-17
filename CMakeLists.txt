cmake_minimum_required(VERSION 3.5)

project(concorde)

# Use ament instead of catkin
find_package(ament_cmake REQUIRED)

# Install folders (same as before, but ROS2 style destination)
install(
  DIRECTORY config launch meshes urdf
  DESTINATION share/${PROJECT_NAME}
)

# Required for ament packages
ament_package()