import 'package:flutter/material.dart';

import 'feature_flags.dart';

void main() {
  runApp(const DemoApp());
}

class DemoApp extends StatefulWidget {
  const DemoApp({super.key});

  @override
  State<DemoApp> createState() => _DemoAppState();
}

class _DemoAppState extends State<DemoApp> {
  // Point this at wherever uvicorn is running. On the Android emulator use
  // 10.0.2.2 instead of 127.0.0.1.
  final flags = FeatureFlags(host: '127.0.0.1:8000');

  @override
  void initState() {
    super.initState();
    flags.load();
    flags.connect();
  }

  @override
  void dispose() {
    flags.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: flags,
      builder: (context, _) {
        return MaterialApp(
          title: 'Remote Config Demo',
          theme: ThemeData(
            useMaterial3: true,
            colorSchemeSeed: Colors.indigo,
            brightness: flags.isEnabled('dark_mode_beta')
                ? Brightness.dark
                : Brightness.light,
          ),
          home: HomePage(flags: flags),
        );
      },
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key, required this.flags});

  final FeatureFlags flags;

  @override
  Widget build(BuildContext context) {
    final welcome = flags.config('welcome_message') ?? 'Welcome';

    return Scaffold(
      appBar: AppBar(
        title: const Text('My App'),
        centerTitle: true,
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                Text(
                  welcome,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                const SizedBox(height: 24),
                if (flags.isEnabled('new_checkout_flow'))
                  FilledButton(
                    onPressed: () {},
                    child: const Text('Try the new checkout'),
                  )
                else
                  OutlinedButton(
                    onPressed: () {},
                    child: const Text('Checkout'),
                  ),
                const SizedBox(height: 40),
                Text(
                  'Toggle a flag from the terminal dashboard and this screen '
                  'updates on its own — no reload, no restart.',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
