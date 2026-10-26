# Armando — Wrist Camera and Arm Control
 
**Robotics Lab 2026 · Classwork 1**
 
This repository extends the `armando_description` package with:
 
1. a **second camera mounted on the wrist** of the manipulator, whose images are bridged from Gazebo to ROS 2;
2. **two alternative control nodes** for the arm, one in C++ (predefined pose sequence) and one in Python (keyboard teleoperation).
 
The instructions below go from a clean machine to a running simulation, and show how to validate every task of the assignment.
 
---
 
## Repository structure
 
```
src/
├── armando_description/      # robot model: URDF/XACRO, meshes, configs, Gazebo launch
├── armando_controller_cpp/   # C++ node: sends the arm through a sequence of predefined poses
└── armando_controller_py/    # Python node: keyboard teleoperation of the arm joints
```
 
The workspace keeps the **robot description** separate from the **control logic**.
 
- `armando_description` defines *what the robot is*: geometry, joints, sensors and Gazebo integration.
- The `armando_controller_*` packages define *how the robot is commanded*: nodes that publish commands to the arm controller.
 
 
> **Note:** technically, a control node could also be placed inside `armando_description`, and it would still work. This is **not** considered best practice: a `*_description` package should contain only the robot model. Adding executable nodes mixes different responsibilities and makes the package harder to reuse and maintain.
 
---
 
## Prerequisites
 
- Docker installed on the host machine
- The Classwork 0 repository (`<surname>_rl26`), which contains the Docker scripts
 
---
 
## 1. Setup
 
### 1.1 Clone the repository
 
```bash
git clone https://github.com/RoboticsLab2026/armando_classwork1
```
 
Then copy the downloaded packages into the `src` directory of your Classwork 0 workspace (`<surname>_rl26/src`).
 
### 1.2 Build the Docker image
 
If an image from a previous classwork already exists, remove it and build a new one under a different name:
 
```bash
docker images                 # find the ID of the old image
docker rmi <IMAGE_ID>         # remove it
cd ../docker_scripts
./docker_build_image.sh armando_img
```
 
### 1.3 Start the container
 
```bash
./docker_run_container.sh
```
 
The `<surname>_rl26/src` directory must be mounted in the container workspace (`/home/user/ros2_ws/src`). The source code then lives on the host and survives when the container is closed.
 
---
 
## 2. Build the workspace and install dependencies
 
Inside the container:
 
```bash
cd /home/user/ros2_ws
rosdep update
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
source install/setup.bash
```
 
`rosdep` reads each `package.xml`, maps the ROS dependencies to Ubuntu packages and installs them. If an installation fails, run `sudo apt update` first (the container password is `user`).
 
> Dependencies installed this way are **lost when the container is closed**, so repeat this step at every new session. To make them persistent, add them to the Dockerfile.
 
---
 
## 3. Task 1: Launch the simulation
 
**Terminal 1**: start Gazebo with Armando:
 
```bash
ros2 launch armando_description armando_gazebo.launch.py
```
 
**Terminal 2**: open a second shell in the same container:
 
```bash
./docker_connect
cd /home/user/ros2_ws && source install/setup.bash
```
 
Check that the controllers are active:
 
```bash
ros2 control list_controllers
```
 
Send a test configuration to the arm:
 
```bash
ros2 topic pub --once /joint_trajectory_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory "{
    joint_names: ['j0', 'j1', 'j2', 'j3'],
    points: [{ positions: [0.5, -0.3, 0.8, 0.0], time_from_start: { sec: 2, nanosec: 0 } }]
  }"
```
 
✅ **Checkpoint:** the arm reaches the commanded configuration in about 2 seconds.
 
---
 
## 4. Task 2: Verify the wrist camera
 
The wrist camera is declared in the XACRO description with its own link, joint, optical frame and `<gazebo>` sensor block. Its parent is the end effector, so it moves with the kinematic chain, unlike the existing camera, which is fixed to `base_link`. The camera has its own topic name and its own entry in the Gazebo–ROS bridge of the launch file.
 
With the simulation running, from **Terminal 2**:
 
```bash
ros2 topic list | grep camera_2        # the wrist camera topic must be listed
ros2 topic hz /camera_2/image          # images must be published at a steady rate
```
 
Then open the image viewer:
 
```bash
rqt
```
 
In `rqt`, select **Plugins → Visualization → Image View**, then choose the wrist camera topic from the drop-down menu.
 
✅ **Checkpoint:** the wrist camera stream is visible in `rqt`.
 
---
 
## 5. Task 3: Move the arm
 
Two alternative solutions are provided. Keep the simulation running in Terminal 1 and the wrist camera open in `rqt`, then use **one** of the following nodes in a new terminal.
 
### Solution A: Predefined pose sequence (C++)
 
```bash
ros2 launch armando_controller_cpp controller_launch.py
```
 
The node is started through a Python launch file and sends the arm through a sequence of predefined joint configurations, with no user input.
 
### Solution B: Keyboard teleoperation (Python)
 
```bash
ros2 run armando_controller_py armando_keyboard_teleop.py
```
 
The node reads keyboard input and moves the arm joints interactively.
 
 
✅ **Checkpoint:** the arm moves in Gazebo and the wrist camera image in `rqt` moves with it.
 
---

