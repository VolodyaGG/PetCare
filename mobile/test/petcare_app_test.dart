import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:petcare/app/petcare_app.dart';
import 'package:petcare/core/network/api_client.dart';

void main() {
  testWidgets('opens the base screens and retries the server check', (
    tester,
  ) async {
    final firstCheck = Completer<void>();
    var checks = 0;
    await tester.pumpWidget(
      PetCareApp(
        checkBackend: () {
          checks++;
          return checks == 1 ? firstCheck.future : Future<void>.value();
        },
      ),
    );
    expect(find.text('Список питомцев пока пуст.'), findsOneWidget);

    await tester.tap(find.text('Задачи'));
    await tester.pumpAndSettle();
    expect(find.text('Задач по уходу пока нет.'), findsOneWidget);

    await tester.tap(find.text('Настройки'));
    await tester.pumpAndSettle();
    final checkButton = find.text('Проверить подключение');
    expect(checks, 0);
    await tester.tap(checkButton);
    await tester.pump();
    expect(find.text('Проверяем подключение…'), findsOneWidget);

    firstCheck.completeError(
      const ApiException('database_unavailable', 'Database unavailable'),
    );
    await tester.pumpAndSettle();
    expect(find.text('База данных недоступна.'), findsOneWidget);

    await tester.tap(checkButton);
    await tester.pumpAndSettle();
    expect(find.text('Сервер и база данных доступны.'), findsOneWidget);

    await tester.tap(find.text('Питомцы'));
    await tester.pumpAndSettle();
    expect(find.text('Список питомцев пока пуст.'), findsOneWidget);
  });
}
