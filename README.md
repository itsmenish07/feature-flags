# Feature Flags & Remote Config System

A lightweight DIY alternative to LaunchDarkly and Firebase Remote Config.
Flip a switch on the server and connected clients update in real time, no
reload or restart needed.

## Features

- Create feature flags and toggle them on/off
- Store remote configs (text or numbers)
- Target specific groups (e.g. beta testers)
- Percentage rollouts (consistent per user)
- Real-time updates over WebSockets
- Terminal dashboard to manage everything
- Flutter client + example app

## Tech Stack

- FastAPI
- SQLite
- SQLAlchemy
- WebSockets
- Textual
- Flutter (client)

## Setup

```bash
pip install -r requirements.txt
```

The database (`flags.db`) is created on first run and is not committed, so a
fresh clone starts empty. Load some demo flags and configs with:

```bash
python seed.py
```

## Run the server

```bash
uvicorn main:app --reload
```

API docs are at http://127.0.0.1:8000/docs. CORS is open, so a browser-based
client (e.g. Flutter web) can call the API directly.

## Terminal dashboard

With the server running:

```bash
python dashboard.py
```

- `Tab` switch between flags and configs
- `↑ ↓` move
- `Space` toggle a flag
- `Enter` edit a flag rule (group, rollout %) or a config value
- `D` delete the selected flag or config
- `R` refresh
- `Q` quit

The dashboard subscribes to the WebSocket, so changes made elsewhere (the API,
another dashboard, the Flutter app) show up live without pressing `R`.

## WebSocket client

A minimal example that prints changes as they happen:

```bash
python client.py
```

## Flutter client

A small Flutter app under `flutter_client/` loads flags over REST and stays in
sync over the WebSocket. See [flutter_client/README.md](flutter_client/README.md).

## API

| Method | Path | Description |
| --- | --- | --- |
| GET | `/flags` | List all flags |
| POST | `/flags` | Create a flag (`name`, `target_group`, `rollout_percentage`) |
| PUT | `/flags/{id}` | Toggle a flag on/off |
| PUT | `/flags/{id}/rule` | Update `target_group` / `rollout_percentage` |
| DELETE | `/flags/{id}` | Delete a flag |
| GET | `/flags/group/{group}` | Flags for a group (plus `everyone`) |
| GET | `/flags/user/{user_id}/{group}` | Flags a specific user should get |
| GET | `/configs` | List configs |
| POST | `/configs` | Create a config (`key`, `value`) |
| PUT | `/configs/{id}` | Update a config value |
| DELETE | `/configs/{id}` | Delete a config |
| WS | `/ws` | Live flag/config updates |

Config values are stored as strings (like Firebase Remote Config). Read them
with a typed accessor on the client — the Flutter client has `config()` for
strings and `configInt()` for numbers.

## Tests

```bash
pytest
```

Each test runs against a throwaway SQLite database, so it won't touch
`flags.db`.
