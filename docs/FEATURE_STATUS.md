# Specification coverage

This ZIP is an implemented simulator edition, not completion of every production requirement.

| Area | Implemented | Remaining |
|---|---|---|
| Frontend | React/TypeScript, dark responsive shell, 11 pages | Tailwind/shadcn/Zustand not used; plain CSS and React state |
| Simulator | Differential-drive kinematics, heading, telemetry, fault injection | Physical dynamics, realistic battery/thermal models |
| Control | Hold buttons, speed, mode, server dead-man, stop | Analog joystick/gamepad |
| Missions | Create, edit, reorder, duplicate, delete, route click editor, start/pause/resume/abort, dwell, return home | Patrol cycles, exploration, waypoint actions beyond dwell, ETA |
| Navigation | Offline local map, trail, heading, geofence | GIS layers, satellite, RTK integration, SLAM, path replanning |
| Cameras | Four synthetic canvas scenes, fullscreen, PNG snapshots, offline simulation | Live capture, WebRTC, video recording/audio/PTZ |
| Sensors | Labeled simulated GPS, IMU, encoders, ranges, LiDAR metadata, battery, motors, network | Real adapters, LiDAR point clouds, comprehensive calibration |
| Perception | Protocol and labeled synthetic obstacle fixture | Trained detection/tracking/free-space models |
| Safety | Latched stop, owner lease, acceleration/speed bounds, stale/reordered command rejection, low battery, GPS/sensor/motor faults, geofence | Physical safety qualification and hardware E-stop integration |
| Data | SQLAlchemy, SQLite default, PostgreSQL Compose, retention, CSV/JSON, audit | Normalized production schema, migrations, video archive |
| Authentication | ADMIN/OPERATOR/VIEWER, scrypt, cookies, CSRF, origin checks, throttling | Password recovery, account removal, MFA, shared session store |
| ROS | Driver protocol and documented topic mapping | Executable ROS adapter and hardware validation |
| Deployment | Local start scripts, prebuilt UI, Docker/Compose configuration | Production deployment verification, horizontal scale |
| Testing | Backend state-machine/API tests, frontend TypeScript/build | Browser visual/interactivity checks, hardware-in-loop, load testing, frontend component suite |

The simulator intentionally uses a conservative stop for every critical fault. Fault responses
are not configurable to unsafe alternatives. All camera/perception output is labeled synthetic.
