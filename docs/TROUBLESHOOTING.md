# Troubleshooting

- Use Python 3.12 for this tested dependency set. On Windows use `py -3.12`, not an unrelated
  system Python 3.14 environment. No OpenCV or NumPy compilation is required to run the simulator.
- Run commands inside the extracted `rover-control-center` directory containing README.md.
- PowerShell activation is optional: use `.\.venv\Scripts\python.exe` directly.
- If the port is busy, set PORT before using scripts/start.py, or close the other local server.
- Missing frontend: run `npm ci` then `npm run build` from frontend. Use Node 22 LTS.
- Sign-in: use the admin password from the FIRST launch. Changing ADMIN_PASSWORD does not reset
  an existing account. For disposable simulation data only, stop the server, back up rover.db and
  move it aside to create a fresh database. This also starts with an empty mission/history store.
- Cannot move: acquire control, clear injected faults, reset latched safety, choose MANUAL and
  hold a direction. VIEWER accounts cannot control. Browser focus/background changes stop motion.
- Mission start rejected: acquire control, select AUTONOMOUS, check route speed and geofence.
- Stale telemetry: inspect backend console, reload and log in if the server restarted.
- Reverse proxy: preserve Host/Origin and WebSocket upgrades, terminate TLS correctly and set
  COOKIE_SECURE=true for HTTPS. Never use multiple uvicorn workers with the in-memory controller.
- Compose password: use URL-safe characters for POSTGRES_PASSWORD or encode the database URL.
- Synthetic scenes are intentional. There is no physical camera, AI model or ROS adapter configured.
