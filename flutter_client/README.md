# Flutter client

A small Flutter app that consumes the feature flag server. It loads flags and
configs over REST once, then listens on the websocket so changes show up live.

## Setup

```bash
cd flutter_client
flutter pub get
flutter run
```

Make sure the server is running first:

```bash
uvicorn main:app --reload
```

If you run on the Android emulator, change the host in `lib/main.dart` from
`127.0.0.1:8000` to `10.0.2.2:8000`.

## Using it in your own app

`lib/feature_flags.dart` is the reusable part. It is a `ChangeNotifier`, so it
works with `AnimatedBuilder`, `ListenableBuilder` or Provider.

```dart
final flags = FeatureFlags(
  host: '127.0.0.1:8000',
  userId: 'user-123',   // optional, enables percentage rollouts
  group: 'beta',        // optional target group
);

await flags.load();
flags.connect();

if (flags.isEnabled('new_checkout_flow')) {
  // show the new screen
}

final welcome = flags.config('welcome_message');
final attempts = flags.configInt('max_login_attempts', fallback: 3);
```

Toggle a flag from the terminal dashboard or `PUT /flags/{id}` and any widget
reading `flags` rebuilds on its own.
