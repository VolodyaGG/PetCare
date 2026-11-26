# Первый спринт: задачи Вовы

| Задача плана | Реализация | Статус |
| --- | --- | --- |
| Выбрать framework и API | FastAPI, SQLAlchemy, `/api/v1`, единые ошибки, OpenAPI | Подготовлено |
| Локальное серверное окружение | Dockerfile, Compose: db → migrate → api | Подготовлено; запуск Compose ещё не проверен |
| Поднять PostgreSQL | PostgreSQL 18, volume, healthcheck, loopback-порт | Конфигурация готова; работающая база в этой сессии не поднята |
| Миграции и подключение | Alembic, baseline, Session, settings, readiness | Код готов; онлайн-миграции требуют проверки с БД |
| Базовый backend и `/health` | Проверка `SELECT 1`, 200/503 без утечки секретов | Реализовано; unit-тесты прошли |
| CI backend | Lint, format, unit/integration, образ, Compose config | Workflow готов; удалённый запуск не выполнен |
| CI Flutter | Format, analyze, tests, iOS simulator build на macOS | Workflow готов; ждёт `mobile/` Кирилла |
| Согласовать API | Документы для Кирилла, Егора и Артура, схема AI JSON | Предложение готово; подтверждение команды отсутствует |
| Review кода Артура | Инструкция и критерии review | Ожидает модели и endpoint Артура |

Сервер, HTTPS, публикация и автоматический деплой исключены по запросу.
Flutter-приложение, STT, LLM, пользовательские модели и demo endpoint назначены
другим участникам и в работу Вовы не включены.

Проверено локально: 11 unit-тестов, Ruff lint и format, конфигурация Compose,
генерация SQL миграции в offline-режиме и генерация OpenAPI/JSON Schema.
Интеграционный тест пропущен: отсутствует доступная одноразовая PostgreSQL-база.

Ограничения проверки в этой сессии: Docker daemon недоступен; локальный PostgreSQL
при initdb получает `Operation not permitted` на создании shared memory.
Сеть shell недоступна; зависимости для unit-тестов установлены из локального кэша.
Оставшиеся интеграционные проверки описаны в README и настроены в backend CI.
Успешный запуск БД и удалённого CI пока не подтверждён.
