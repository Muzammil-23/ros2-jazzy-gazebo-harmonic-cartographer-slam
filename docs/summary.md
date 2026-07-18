# Summary — Lessons Learned

This document covers every significant issue encountered during the ROS 2 Jazzy + Gazebo Harmonic + Cartographer SLAM integration. Each section describes the symptom, root cause, and fix. If you are starting a similar project, read this first.

---

## 1. The Sensors System Plugin is Mandatory in the World SDF

**Symptom:** Sensor spawns correctly, appears in Gazebo scene, but `gz topic -l` shows no sensor topic, or the topic exists but `gz topic -e` returns nothing.

**Root cause:** Gazebo Harmonic separates sensor activation from sensor definition. A sensor defined in an SDF or URDF is parsed and attached to the model, but it will never produce data unless `gz::sim::systems::Sensors` is loaded in the **world** SDF. The default `empty.sdf` does not include this plugin. No error or warning is thrown, sensors simply do nothing.

**Fix:** Create a custom world SDF and include the plugin explicitly:
```xml
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
```
Launch Gazebo with this world instead of `empty.sdf`.

---

## 2. URDF Sensor Blocks are Ignored by Gazebo Harmonic

**Symptom:** `<gazebo reference="laser_link">` sensor block in URDF, robot spawns, `laser_link` appears in TF tree, but no sensor topic is published. `gz topic -l | grep lidar` returns nothing.

**Root cause:** Gazebo Harmonic's URDF parser handles `<gazebo reference>` sensor blocks inconsistently. The sensor is parsed but not registered with the sensor system. This is a known limitation of the URDF→SDF translation layer in gz-sim8.

**Fix:** Define the sensor in a standalone SDF file and spawn it as a separate model. The sensor must be in native SDF format for Gazebo Harmonic to activate it properly.

---

## 3. SDF Sensor Tag: `<lidar>` not `<ray>`

**Symptom:** Sensor SDF is valid, model spawns, Sensors plugin is loaded, but still no data.

**Root cause:** Gazebo Classic used `<ray>` as the sensor body tag. Gazebo Harmonic uses `<lidar>`. Using `<ray>` results in silent failure — the sensor type is not recognized.

**Fix:**
```xml
<!-- Wrong (Gazebo Classic) -->
<ray>...</ray>

<!-- Correct (Gazebo Harmonic) -->
<lidar>...</lidar>
```

---

## 4. Plugin Names are Fully-Qualified C++ Class Names

**Symptom:** `[Err] [SystemLoader.cc:92] Failed to load system plugin` even though the `.so` file exists on disk.

**Root cause:** The `name` attribute in a `<plugin>` block must match the fully-qualified C++ namespace of the plugin class, not the filename and not an arbitrary label. A single wrong character causes silent failure or a cryptic error.

**Correct names for gz-sim8:**
```
gz::sim::systems::VelocityControl     → libgz-sim8-velocity-control-system.so
gz::sim::systems::DiffDrive           → gz-sim-diff-drive-system
gz::sim::systems::Sensors             → gz-sim-sensors-system
gz::sim::systems::Physics             → gz-sim-physics-system
gz::sim::systems::SceneBroadcaster    → gz-sim-scene-broadcaster-system
gz::sim::systems::UserCommands        → gz-sim-user-commands-system
gz::sim::systems::JointStatePublisher → gz-sim-joint-state-publisher-system
```

**How to verify:** Run `gz sim --system-plugin-info` or check the error output, Gazebo lists available plugin names when a load fails.

---

## 5. Mesh Paths: Use `file:///` not `package://`

**Symptom:** `[Err] [SystemPaths.cc:426] Unable to find file with URI [model://robot/meshes/base_link.STL]`

**Root cause:** Gazebo Classic resolved `package://` URIs via ROS package paths. Gazebo Harmonic uses its own resource system (`model://`) or filesystem paths (`file:///`). `package://` URIs are not resolved by Gazebo Harmonic.

**Fix:** Use absolute `file:///` paths in the Xacro:
```xml
<xacro:property name="mesh_dir"
  value="file:///home/user/ros2_ws/install/package/share/package/meshes/"/>
```

---

## 6. The Clock Must be Bridged from Gazebo

**Symptom:** Cartographer starts, receives scans, but never publishes the `map` TF frame. RViz shows `frame [map] doesn't exist`. `/map` topic is silent.

**Root cause:** Cartographer uses `use_sim_time` to timestamp its operations. Without bridging `/clock` from Gazebo, ROS nodes run on wall clock time while scan messages carry Gazebo sim timestamps. Cartographer sees the mismatch and silently discards every scan.

**Fix:** Add the clock to the bridge arguments:
```python
'/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
```
Use `[` (unidirectional, Gazebo→ROS) not `@` (bidirectional) for the clock.

---

## 7. Static Transforms and Sim Time Don't Mix Well

**Symptom:** TF tree is complete (`odom → base_link → laser_link` all present), but Cartographer still discards scans. `ros2 topic echo /tf_static` shows all transforms stamped at `sec: 0`.

**Root cause:** `static_transform_publisher` with `use_sim_time: true` waits for a clock message before publishing, but stamps transforms at time 0 regardless. Cartographer looks up the `base_link → laser_link` transform at the scan's timestamp (e.g. `sec: 43`) and finds nothing in the TF buffer at that time.

**Fix:** Run static transform publishers **without** `use_sim_time`. Static transforms are valid for all time, they don't need sim time. Cartographer's `lookup_transform_timeout_sec` handles the mismatch.

---

## 8. The Sensors Plugin Requires a Rendering Engine

**Symptom:** `gpu_lidar` sensor produces no data even with the Sensors plugin loaded.

**Root cause:** `gpu_lidar` uses GPU-based ray casting via the ogre2 rendering engine. On machines without a capable GPU or without ogre2 configured, the sensor silently fails.

**Fix:** Specify the render engine explicitly in the Sensors plugin:
```xml
<plugin filename="gz-sim-sensors-system"
        name="gz::sim::systems::Sensors">
  <render_engine>ogre2</render_engine>
</plugin>
```
If GPU rendering is unavailable, switch from `type="gpu_lidar"` to `type="lidar"` (CPU-based) in the sensor SDF.

---

## 9. Cartographer Lua — Required Fields Vary by Version

**Symptom:** `cartographer_node` crashes on startup with a stack trace ending in `GetBool()` inside `CreateTrajectoryOptions()`.

**Root cause:** Different versions of Cartographer ROS require different subsets of boolean fields in the Lua config. Missing any required field causes an immediate crash with a non-obvious error message.

**Fields required for ROS 2 Jazzy / Cartographer on Ubuntu 24.04:**
```lua
publish_frame_projected_to_2d = false,
use_pose_extrapolator = true,
publish_tracked_pose = false,
```
These are not in older tutorials or the TurtleBot3 config — they must be added manually.

---

## 10. Cartographer Executable Name Changed

**Symptom:** `ros2 run cartographer_ros occupancy_grid_node` — executable not found.

**Root cause:** The executable was renamed between versions.

**Fix:**
```bash
# Wrong
occupancy_grid_node

# Correct
cartographer_occupancy_grid_node
```
Always verify with: `ls /opt/ros/jazzy/lib/cartographer_ros/`

---

## 11. ros_gz_bridge Topic Strings are Exact and Case-Sensitive

**Symptom:** Bridge starts without errors, `/scan` appears in `ros2 topic list`, but `ros2 topic echo /scan` returns nothing.

**Root cause:** The bridge argument must match the exact Gazebo topic path, including all namespace components. The message type on both sides must also match exactly.

**How to find the real Gazebo topic:**
```bash
gz topic -l | grep scan
gz topic --info --topic /scan
```

**Correct bridge argument format:**
```
/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan
```
Use `[` for Gazebo→ROS (unidirectional). Use `@` only for bidirectional topics like `cmd_vel`.

---

## 12. Two-Launch Architecture Works Better Than One

**Problem:** A single launch file with timer delays for spawning is fragile, if Gazebo takes longer than expected to load, all spawners time out and the entire launch fails silently.

**Solution:** Split into two launch files following TurtleBot3's pattern:
- `gazebo.launch.py` — Gazebo, robot spawn, bridge, static transforms
- `cartographer.launch.py` — Cartographer node and occupancy grid node

Launch Gazebo first, wait for the robot to appear visually, then launch Cartographer. This decouples timing completely and makes debugging much easier since each layer can be restarted independently.

---

## 13. Nav2 Requires Real Odometry

**Status:** Not implemented (Phase 3).

Nav2's AMCL localizer requires a continuously updating `odom → base_link` transform published by wheel encoders or an IMU. The `VelocityControl` plugin used in this project does not publish odometry. A static `odom → base_link` transform was used as a placeholder for SLAM mapping, but this will not work for Nav2.

**What is needed for Phase 3:**
- Replace `VelocityControl` with `gz::sim::systems::DiffDrive`
- Bridge `/model/robot/odom` and `/tf` from Gazebo to ROS
- Remove static `odom → base_link` transform publisher
- Update Cartographer Lua: `use_odometry = true`, `published_frame = "odom"`

---

## TL;DR — The Five Things That Waste the Most Time

1. **Not having the Sensors plugin in the world SDF.** Every sensor is dead without it. No error. Nothing.
2. **Using `empty.sdf` as the Gazebo world.** It has no Sensors plugin. Make your own world SDF.
3. **Wrong plugin names.** They are C++ namespaces, not filenames. Check before writing.
4. **Not bridging the clock.** `use_sim_time` without a clock bridge silently breaks everything timestamp-related.
5. **Trying to put sensors in URDF `<gazebo reference>` blocks.** It doesn't work reliably in Gazebo Harmonic. Use standalone SDF files.
