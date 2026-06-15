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

## Prerequisites

- Python 3.10+
- Git
- Flutter SDK (only needed to run the Flutter client)

## Setup (step by step)

### 1. Clone the repo

```bash
git clone https://github.com/itsmenish07/feature-flags.git
cd feature-flags
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv venv
```

Activate it:

```bash
# Windows (PowerShell)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

Then install:

```bash
pip install -r requirements.txt
```

### 3. Seed demo data

The database (`flags.db`) is created on first run and is not committed, so a
fresh clone starts empty. Load some demo flags and configs with:

```bash
python seed.py
```

### 4. Run the server

```bash
uvicorn main:app --reload
```

The API is now at http://127.0.0.1:8000 (interactive docs at `/docs`). CORS is
open, so a browser-based client (e.g. Flutter web) can call it directly. Leave
this terminal running.

### 5. Run the terminal dashboard (new terminal)

Activate the virtual environment again, then:

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

### 6. Run the Flutter client (new terminal)

```bash
cd flutter_client
flutter pub get
flutter run -d chrome    # or: flutter run  (pick a device)
```

The app loads flags over REST and stays in sync over the WebSocket. If the
server is not on the same machine, change `host` in `flutter_client/lib/main.dart`
(on the Android emulator use `10.0.2.2:8000` instead of `127.0.0.1:8000`).

## Demo walkthrough

Put the Flutter app (or browser) and the terminal dashboard side by side, then:

1. In the dashboard, move to `dark_mode_beta` and press `Space`. The app
   instantly switches between light and dark theme — no reload.
2. Press `Enter` on the `welcome_message` config, type a new message. The app's
   heading updates live.
3. Toggle `new_checkout_flow` off and on. The checkout button in the app changes.

This is the core idea: flip a switch on the server, every connected client
updates in real time.

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

Backend (10 tests, run from the project root with the virtual environment
active):

```bash
pytest
```

Each test runs against a throwaway SQLite database, so it won't touch
`flags.db`.

Flutter client (3 tests):

```bash
cd flutter_client
flutter test
```

Neither suite needs the server running — they spin up their own in-process
server.
