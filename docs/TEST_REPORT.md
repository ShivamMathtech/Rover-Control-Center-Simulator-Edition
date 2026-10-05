# Verification report

Tested in Linux with Python 3.12 and Node 24.19.0 on 2026-10-05.

- `python -m pytest -q tests`: **22 passed**.
- `npm run build`: TypeScript strict compile and Vite production build passed.
- FastAPI startup with a file-backed SQLite database succeeded.
- Authenticated API tests cover mission CRUD and transitions, control ownership, role restrictions,
  CSRF, exports, auditing, WebSocket connect/reconnect and database persistence across restart.
- Controller tests cover dead-man timeout, latched emergency stop, all critical simulated faults,
  explicit reset, stale/reordered command rejection, exclusive control, mission completion/dwell,
  lease loss, geofence prediction, speed bounds, pause/resume and mode change.
- Hardware mode startup is tested to fail closed.

A browser visual/interactivity smoke test could not run: the available Playwright runtime had no
installed browser, and the browser download returned an invalid archive. Browser appearance and
pointer interactions therefore remain unverified beyond TypeScript/build checks. Docker/PostgreSQL,
Windows startup, physical hardware, ROS and real camera streams were not executed in this environment.

The backend tests emit one upstream Starlette/AnyIO deprecation warning; no test failures.
