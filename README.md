# MathTech Rover Control Center — Simulator Edition

A runnable, non-weaponized rover operations application built from the supplied specification.
React + TypeScript frontend, FastAPI backend, SQLAlchemy persistence, a deterministic rover simulator,
authenticated WebSocket telemetry, mission execution and server-enforced safety controls.

**This release is a simulation application, not a production-qualified physical rover controller.**
The original 52-section specification is included in `docs/ORIGINAL_SPECIFICATION.txt`.
Implemented and outstanding capabilities are recorded in `docs/FEATURE_STATUS.md`.
Hardware mode fails explicitly. Camera scenes and perception annotations are synthetic.

## Start on Windows (recommended)

Install Python 3.12, extract the ZIP, and open PowerShell inside `rover-control-center`.
The ZIP includes a prebuilt frontend, so Node.js is not required just to run it.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe scripts\start.py
```

Enter your own admin password (at least 12 characters) when prompted.
Open **http://127.0.0.1:8000** and sign in as **admin** with that password.
After installing dependencies, you can also double-click `start-windows.bat`.
The initial admin password is persisted as a salted scrypt hash; entering a different
password on later launches does not change the existing account password.

## macOS / Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python scripts/start.py
```

Initial dependency installation needs internet. The running simulator, charts and local map do not.
SQLite data is saved as `rover.db` in the project root. Do not delete it to update the code.

## Try the workflow

1. Sign in, click **Acquire control**, and leave mode as MANUAL.
2. Open **Rover control** and hold an arrow. Release to stop. The backend stops
   stale manual commands after 0.6 s, independently of UI input handling.
3. Change mode to AUTONOMOUS. Open **Missions**, load `Inspection loop`, then Start.
4. Watch the route, trail, speed and waypoint progress in Overview.
5. Pause/resume from Overview. Abort ends the current mission.
6. Inject GPS loss, an obstacle or another fault in Diagnostics. Motion stops and latches.
7. Clear the fault, acquire control if needed, and press **Reset safety** on Rover control.
   Reset never restarts movement. Start a mission or hold a direction again explicitly.
8. View Telemetry and export CSV/JSON. Review Event log. Create viewer/operator accounts in Settings.

Only one authenticated session owns motion control. A visible controlling tab renews its lease
at 2 Hz. Closing, backgrounding or disconnecting that tab stops autonomous motion after the
configured link timeout (2 s default). Reconnecting does not automatically acquire control.
The software stop is a simulator feature and does not replace a physical emergency-stop circuit.

## Frontend development

Use Node.js 22 LTS. Run the backend in one terminal:

```powershell
$env:ADMIN_PASSWORD = "Mathtechadmin123"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Use the Vite URL printed in the terminal. Its proxy forwards API and WebSocket traffic.
Rebuild the packaged frontend after edits with `npm run build`.

## Docker with PostgreSQL

Copy `.env.example` to `.env`, fill both passwords, then run:

```bash
docker compose up --build
```

Use a URL-safe alphanumeric `POSTGRES_PASSWORD` for the Compose connection URL.
Open http://127.0.0.1:8000. PostgreSQL persists in a Docker volume.
The container combines the UI, API and simulator; Redis and a separate simulator process
are unnecessary for this single-rover edition. Docker deployment is supplied but was not
executed in the build environment; local SQLite operation was tested.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q tests
```

Frontend compile: `cd frontend && npm ci && npm run build`.
See `docs/TEST_REPORT.md` for checks actually performed.

## Important operating constraints

- Run **one backend worker**. The controller and session lease are in memory; multiple workers
  would create independent simulator states. Restart invalidates sessions and aborts active missions.
- This is a local simulation tool. Remote deployment needs HTTPS, `COOKIE_SECURE=true`,
  a trusted reverse proxy, operational monitoring, dependency review and deployment-specific testing.
- Map is an offline east/north grid in metres around a simulated home in Dehradun. It is not
  a GIS/satellite map. Displayed GPS coordinates use a short-range approximation.
- Assisted mode currently uses the same conservative stop-on-obstacle policy as manual mode.
  No path replanning or SLAM is implemented.
- Browser snapshots save synthetic PNGs locally. WebRTC, physical cameras, video recording,
  real AI inference and ROS motor publishing are not implemented in this release.

Documentation: `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/HARDWARE.md`,
`docs/FEATURE_STATUS.md`, `docs/TROUBLESHOOTING.md`.
