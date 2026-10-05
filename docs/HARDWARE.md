# Hardware integration boundary (not implemented)

`backend/app/drivers.py` defines RoverDriver and PerceptionEngine protocols.
Only SimulatorDriver is implemented. Setting MODE=hardware raises an explicit startup error.
This package contains no actuator publishing code. The topic mapping in `ros2/topics.example.yaml`
is a planning reference, not a working ROS package.

A real deployment needs a platform-specific adapter with connection supervision, timestamped
sensor readings, calibration, measured latency, independently enforced command timeout and a
hardware emergency-stop. Add adapters and bench tests before changing the fail-closed startup guard.
A real sensor API must report validity, units and sample timestamps and reject stale data.

Suggested ROS 2 message mapping: Twist for velocity; Odometry for wheel odometry;
NavSatFix for GPS; Imu for IMU; LaserScan for LiDAR; BatteryState for battery.
Topic names and frame IDs must match the robot and remain configurable. Navigation requires
frame transforms and actual localization, geofence coordinates and validated collision handling.

For cameras, implement camera capture and a WebRTC signaling/media service, bound to authenticated
users. Send only metadata through REST. Monitor disconnects and expose actual FPS/latency.
For AI, implement PerceptionEngine with explicitly supplied model weights and preprocessing.
Use independent ranging sensors for safety; detector confidence is not a safety guarantee.

No real-world motor control, WebRTC service, SLAM, object tracking, occupancy mapping or trained
model evaluation was performed for this simulator release.
