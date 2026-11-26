# PetCare для iOS

## Запуск на симуляторе iPhone

Нужны macOS, Flutter 3.50.1 или новее и Xcode с установленным iOS Simulator Runtime. После первичной установки Xcode проверьте окружение через `flutter doctor -v`. [Настройка iOS в документации Flutter](https://docs.flutter.dev/platform-integration/ios/setup)

Из корня репозитория найдите доступный iPhone и скопируйте его UDID из вывода `simctl`.

```sh
cd mobile
flutter pub get
xcrun simctl list devices available iPhone
```

Укажите UDID выбранного iPhone. Если он уже запущен, начните с `xcrun simctl bootstatus`.

```sh
IPHONE_UDID=your-device-udid
xcrun simctl boot "$IPHONE_UDID"
xcrun simctl bootstatus "$IPHONE_UDID" -b
flutter run -d "$IPHONE_UDID"
```

В Xcode 26 и более ранних версиях окно симулятора открывается через `open -a Simulator`. Начиная с Xcode 27 используется `open -a DeviceHub`.

## Подключение к backend

По умолчанию клиент обращается к `http://127.0.0.1:8000`. Для локальной проверки запустите backend из [ветки `sprint1-vova`](https://github.com/VolodyaGG/PetCare/tree/sprint1-vova) на том же Mac. Можно использовать отдельную рабочую копию. В этой копии выполните `docker compose up --build -d --wait` и проверьте ответ через `curl --fail http://127.0.0.1:8000/health`.

В приложении откройте **Настройки → Проверить подключение**. Запрос `GET /health` подтверждает доступность сервера и его PostgreSQL. Ошибка `503` с кодом `database_unavailable` отображается как «База данных недоступна».

Чтобы использовать удалённое окружение, задайте HTTPS-адрес без пути `/api/v1`.

```sh
flutter run -d "$IPHONE_UDID" --dart-define=API_BASE_URL=https://api.example.com
```

## Структура

- `lib/app/` содержит каркас приложения и навигацию между вкладками.
- `lib/features/` содержит экраны «Питомцы», «Задачи» и «Настройки».
- `lib/core/network/` содержит JSON-клиент и проверку `/health`.
- `ios/` содержит проект Xcode `Runner`.

Проверки выполняются из `mobile/`.

```sh
dart format --output=none --set-exit-if-changed .
flutter analyze --fatal-infos
flutter test
flutter build ios --simulator --debug
```
