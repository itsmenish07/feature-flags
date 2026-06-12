import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:feature_flags_client/feature_flags.dart';
import 'package:flutter_test/flutter_test.dart';

// Spins up a throwaway HTTP + websocket server so the client can be exercised
// the same way it would talk to the real FastAPI backend.
void main() {
  late HttpServer server;
  final sockets = <WebSocket>[];

  setUp(() async {
    server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    server.listen((req) async {
      if (req.uri.path == '/ws') {
        sockets.add(await WebSocketTransformer.upgrade(req));
        return;
      }

      req.response.headers.contentType = ContentType.json;

      if (req.uri.path == '/flags') {
        req.response.write(jsonEncode([
          {
            'id': 1,
            'name': 'checkout',
            'enabled': false,
            'target_group': 'everyone',
            'rollout_percentage': 100
          }
        ]));
      } else if (req.uri.path == '/configs') {
        req.response.write(jsonEncode([
          {'id': 1, 'key': 'max_login_attempts', 'value': '5'}
        ]));
      } else {
        req.response.write('[]');
      }

      await req.response.close();
    });
  });

  tearDown(() async {
    for (final s in sockets) {
      await s.close();
    }
    sockets.clear();
    await server.close(force: true);
  });

  String host() => '127.0.0.1:${server.port}';

  test('loads flags and configs over REST', () async {
    final flags = FeatureFlags(host: host());
    await flags.load();

    expect(flags.isEnabled('checkout'), isFalse);
    expect(flags.config('max_login_attempts'), '5');
    expect(flags.configInt('max_login_attempts'), 5);
  });

  test('reacts to a flag_update broadcast without reloading', () async {
    final flags = FeatureFlags(host: host());
    await flags.load();
    flags.connect();

    while (sockets.isEmpty) {
      await Future.delayed(const Duration(milliseconds: 20));
    }

    final flipped = Completer<void>();
    flags.addListener(() {
      if (flags.isEnabled('checkout') && !flipped.isCompleted) {
        flipped.complete();
      }
    });

    sockets.first.add(jsonEncode({
      'type': 'flag_update',
      'name': 'checkout',
      'enabled': true,
    }));

    await flipped.future.timeout(const Duration(seconds: 2));
    expect(flags.isEnabled('checkout'), isTrue);

    flags.dispose();
  });

  test('drops a flag on a flag_delete broadcast', () async {
    final flags = FeatureFlags(host: host());
    await flags.load();
    flags.connect();

    while (sockets.isEmpty) {
      await Future.delayed(const Duration(milliseconds: 20));
    }

    final removed = Completer<void>();
    flags.addListener(() {
      if (!flags.flags.containsKey('checkout') && !removed.isCompleted) {
        removed.complete();
      }
    });

    sockets.first.add(jsonEncode({
      'type': 'flag_delete',
      'name': 'checkout',
    }));

    await removed.future.timeout(const Duration(seconds: 2));
    expect(flags.flags.containsKey('checkout'), isFalse);

    flags.dispose();
  });
}
