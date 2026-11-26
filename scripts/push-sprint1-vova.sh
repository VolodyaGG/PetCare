#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
branch=sprint1-vova

if ! git diff --cached --quiet; then
  echo 'Сначала уберите посторонние изменения из staging.' >&2
  exit 1
fi

# Check remote access before changing the local history.
git ls-remote origin HEAD >/dev/null
if git show-ref --verify --quiet "refs/heads/$branch"; then
  git switch "$branch"
else
  git switch -c "$branch"
fi

commit_files() {
  local message="$1"
  shift
  git add -- "$@"
  if ! git diff --cached --quiet; then
    git commit -m "$message"
  fi
}

commit_files 'feat(backend): bootstrap FastAPI with database health checks' \
  .gitignore backend/pyproject.toml backend/requirements.lock backend/requirements-dev.lock \
  backend/app/__init__.py backend/app/main.py backend/app/core backend/app/db \
  backend/app/models backend/app/api backend/app/schemas/__init__.py \
  backend/app/schemas/errors.py backend/tests/test_config.py backend/tests/test_health.py \
  docs/openapi.json

commit_files 'feat(database): configure Alembic migrations and PostgreSQL integration tests' \
  backend/alembic.ini backend/migrations backend/tests/test_database.py

commit_files 'feat(dev): add local Docker Compose environment with PostgreSQL' \
  compose.yaml backend/Dockerfile backend/.dockerignore backend/.env.example

commit_files 'feat(ai): define validated voice command draft contract' \
  backend/app/schemas/voice.py backend/tests/test_voice_contract.py \
  docs/voice-contract.md docs/voice-command.schema.json

commit_files 'ci: add backend checks and Flutter iOS simulator workflow' \
  .github/workflows/backend.yml .github/workflows/flutter.yml

commit_files 'docs: document sprint one setup and team API handoff' \
  README.md docs/api-contract.md docs/backend-handoff.md docs/sprint-1-vova.md \
  scripts/push-sprint1-vova.sh

# Ensure no coauthor trailer was introduced in the new sprint commits.
if git log 617122de3171a7358f89bd0832dd6ef4a05b54db..HEAD --format=%B | \
  grep -Eiq '^Co-authored-by:'; then
  echo 'Обнаружен Co-authored-by. Push остановлен.' >&2
  exit 1
fi

git push --set-upstream origin "$branch"
git log -6 --format='%h %s'
