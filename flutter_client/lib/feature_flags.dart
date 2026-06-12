import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

/// Talks to the feature flag server over REST for the first load and then
/// keeps everything in sync over a websocket. Wrap your app in an
/// [AnimatedBuilder] (or use Provider) and call [isEnabled] / [config] from
/// your widgets.
class FeatureFlags extends ChangeNotifier {
  FeatureFlags({
    this.host = '127.0.0.1:8000',
    this.userId,
    this.group = 'everyone',
  });

  final String host;

  // When a userId is set we ask the server which flags this specific user
  // should get, so percentage rollouts are respected on the client.
  final String? userId;
  final String group;

  final Map<String, bool> _flags = {};
  final Map<String, String> _configs = {};

  WebSocketChannel? _channel;

  bool isEnabled(String name) => _flags[name] ?? false;

  String? config(String key) => _configs[key];

  int configInt(String key, {int fallback = 0}) {
    return int.tryParse(_configs[key] ?? '') ?? fallback;
  }

  Map<String, bool> get flags => Map.unmodifiable(_flags);
  Map<String, String> get configs => Map.unmodifiable(_configs);

  Future<void> load() async {
    await Future.wait([_loadFlags(), _loadConfigs()]);
    notifyListeners();
  }

  Future<void> _loadFlags() async {
    final path = userId == null
        ? '/flags'
        : '/flags/user/$userId/$group';

    final res = await http.get(Uri.parse('http://$host$path'));
    final data = jsonDecode(res.body) as List;

    _flags.clear();
    for (final flag in data) {
      _flags[flag['name'] as String] = flag['enabled'] as bool;
    }
  }

  Future<void> _loadConfigs() async {
    final res = await http.get(Uri.parse('http://$host/configs'));
    final data = jsonDecode(res.body) as List;

    _configs.clear();
    for (final cfg in data) {
      _configs[cfg['key'] as String] = cfg['value'].toString();
    }
  }

  void connect() {
    _channel = WebSocketChannel.connect(Uri.parse('ws://$host/ws'));
    _channel!.stream.listen(
      _handleMessage,
      onError: (_) => _reconnect(),
      onDone: _reconnect,
    );
  }

  void _handleMessage(dynamic raw) {
    final data = jsonDecode(raw as String) as Map<String, dynamic>;

    switch (data['type']) {
      case 'flag_update':
        _flags[data['name'] as String] = data['enabled'] as bool;
      case 'config_update':
        _configs[data['key'] as String] = data['value'].toString();
      case 'flag_delete':
        _flags.remove(data['name'] as String);
      case 'config_delete':
        _configs.remove(data['key'] as String);
      default:
        return;
    }

    notifyListeners();
  }

  bool _closed = false;

  Future<void> _reconnect() async {
    if (_closed) return;
    await Future.delayed(const Duration(seconds: 2));
    if (!_closed) connect();
  }

  @override
  void dispose() {
    _closed = true;
    _channel?.sink.close();
    super.dispose();
  }
}
