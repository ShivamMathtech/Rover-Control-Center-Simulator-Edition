# API reference

Interactive OpenAPI docs: http://127.0.0.1:8000/docs. JSON schema: `/openapi.json`.
Log in through `/api/auth/login` or the UI. Mutation requests require the `X-CSRF-Token`
header matching the `rover_csrf` cookie; Swagger does not populate this header automatically.

| Endpoint | Method | Purpose |
|---|---|---|
| /api/auth/login | POST | username/password, creates cookie session |
| /api/auth/me | GET | current role |
| /api/auth/logout | POST | invalidate session and stop owned rover |
| /api/users | GET, POST | admin user management |
| /api/rovers | GET | simulator rover list |
| /api/rovers/rover-01 | GET | complete snapshot |
| /api/rovers/rover-01/telemetry | GET | complete snapshot |
| /api/rovers/rover-01/sensors | GET | sensor values |
| /api/rovers/rover-01/health | GET | simulation fault status |
| /api/control/acquire | POST | acquire exclusive control lease |
| /api/control/heartbeat | POST | renew current lease |
| /api/rovers/rover-01/command | POST | linear m/s, angular rad/s, sequence, issued_at Unix seconds |
| /api/rovers/rover-01/mode | POST | MANUAL, ASSISTED, AUTONOMOUS |
| /api/rovers/rover-01/stop | POST | zero velocity, abort navigation |
| /api/rovers/rover-01/emergency-stop | POST | latch safety stop |
| /api/rovers/rover-01/reset | POST | explicit safety reset after faults cleared |
| /api/rovers/rover-01/return-home | POST | create and run home mission |
| /api/missions | GET, POST | list/create |
| /api/missions/{id} | PUT, DELETE | edit/delete inactive mission |
| /api/missions/{id}/{action} | POST | start, pause, resume, abort |
| /api/settings | GET, PUT | safety configuration |
| /api/simulator/fault | POST | name + enabled boolean |
| /api/cameras | GET | four synthetic camera metadata entries |
| /api/perception | GET | synthetic annotations; no trained model |
| /api/logs | GET | latest 500 events from last day |
| /api/telemetry/history | GET | seconds=300, at most 3600 latest samples |
| /api/telemetry/export | GET | format=csv or json, seconds up to 86400 |
| /ws | WebSocket | authenticated rover.telemetry envelope |

Errors: 401 no session, 403 role/CSRF restriction, 409 rejected state/safety transition,
422 invalid input, 429 rate exceeded. No endpoint writes to physical motors.

```json
{"name":"Inspection","speed":0.8,"waypoints":[{"x":0,"y":10,"wait":2},{"x":0,"y":0,"wait":0}]}
```

Telemetry source is always `SIMULATION`. Network fault injection models the vehicle link while
keeping the operator/API channel available to clear the fault. Browser/API transport loss is
handled separately through telemetry staleness and the expiring operator lease.
