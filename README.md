# PetCare

iOS-приложение по уходу за питомцами. Backend: Python 3.14, FastAPI, SQLAlchemy 2,
PostgreSQL 18, Alembic. Flutter-проект Кирилл добавляет в `mobile/`.

## Локальный запуск

Нужен работающий Docker с Compose v2:

```sh
docker compose up --build -d --wait
curl --fail http://localhost:8000/health
```

Compose запускает PostgreSQL, ждёт готовности базы, отдельным процессом применяет
миграции и затем запускает API. База хранится в именованном volume. Локальные порты
привязаны к `127.0.0.1`, пароль в Compose — только для разработки.

- API: <http://localhost:8000>
- Swagger: <http://localhost:8000/docs>
- OpenAPI: <http://localhost:8000/openapi.json>
- Логи: `docker compose logs -f api migrate db`
- Остановка с сохранением данных: `docker compose down`

`/health` выполняет `SELECT 1`: `200` — база доступна; `503` — недоступна.
Миграции не выполняются внутри каждого процесса API. После добавления миграций
выполнить `docker compose up --build -d --wait` повторно.

## Разработка без контейнера API

```sh
docker compose up -d db
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip install --no-deps --no-build-isolation -e .
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

Переменные читаются из `backend/.env`, когда команды запускаются из `backend/`.
Изменения `DATABASE_URL` применяются после перезапуска API.

## Проверки

Из `backend/` с установленными dev-зависимостями:

```sh
ruff check .
ruff format --check .
pytest -q -m 'not integration'
```

Для интеграционного теста нужна **отдельная, пустая, одноразовая** PostgreSQL-база:
тест применяет и откатывает миграции. Не указывать рабочую базу приложения.

```sh
TEST_DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/petcare_test pytest -q -m integration
```

Backend CI выполняет lint, форматирование, unit-тесты, миграции upgrade/downgrade,
проверку расхождения ORM/БД, `/health` на PostgreSQL и сборку Docker-образа.
Flutter CI после появления `mobile/pubspec.yaml` выполняет format, analyze, test
и сборку iOS для симулятора на macOS. До этого явно пропускается.
Workflow ничего не публикуют и не развёртывают.

## Документация команды

- [Структура API и контракт для Кирилла](docs/api-contract.md)
- [Формат AI-команд для Егора](docs/voice-contract.md)
- [Структура backend и миграции для Артура](docs/backend-handoff.md)
- [Статус задач Вовы в первом спринте](docs/sprint-1-vova.md)

Контракты подготовлены для обсуждения. Факт согласования с командой не заявлен.
