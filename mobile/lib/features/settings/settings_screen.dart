import 'package:material_ui/material_ui.dart';

import '../../core/network/api_client.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key, required this.checkBackend});

  final Future<void> Function() checkBackend;

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  Future<void>? _healthCheck;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Text(
          'Подключение к серверу',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: 12),
        FutureBuilder<void>(
          future: _healthCheck,
          builder: (context, snapshot) {
            final checking =
                snapshot.connectionState == ConnectionState.waiting;
            final status = switch (snapshot.connectionState) {
              ConnectionState.none => 'Проверка ещё не запускалась.',
              ConnectionState.done when snapshot.hasError => _describeError(
                snapshot.error,
              ),
              ConnectionState.done => 'Сервер и база данных доступны.',
              _ => 'Проверяем подключение…',
            };
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Semantics(liveRegion: true, child: Text(status)),
                const SizedBox(height: 16),
                FilledButton(
                  onPressed: checking ? null : _checkBackend,
                  child: const Text('Проверить подключение'),
                ),
              ],
            );
          },
        ),
      ],
    );
  }

  void _checkBackend() {
    final check = Future<void>.sync(widget.checkBackend);
    setState(() {
      _healthCheck = check;
    });
  }

  String _describeError(Object? error) => switch (error) {
    ApiException(code: 'database_unavailable') => 'База данных недоступна.',
    ApiException(code: 'timeout') => 'Сервер не ответил вовремя.',
    ApiException(code: 'network_error') => 'Не удалось подключиться к серверу.',
    ApiException(code: 'invalid_response') =>
      'Сервер вернул неожиданный ответ.',
    ApiException(statusCode: final int statusCode) =>
      'Ошибка сервера (HTTP $statusCode).',
    _ => 'Не удалось проверить подключение.',
  };
}
