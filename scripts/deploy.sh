#!/usr/bin/env bash
set -euo pipefail

DEPLOY_PATH="$1"
COMMIT_SHA="$2"

cd "$DEPLOY_PATH"

# Не перезаписываем ручные изменения в отслеживаемых файлах.
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "Deployment stopped: tracked files have local changes."
    exit 1
fi

git fetch origin main

# Не разворачиваем устаревший коммит поверх более нового main.
if [ "$(git rev-parse origin/main)" != "$COMMIT_SHA" ]; then
    echo "Deployment stopped: main has a newer commit."
    exit 1
fi

# Берём конфигурацию именно из проверенного коммита.
git checkout --detach "$COMMIT_SHA"

docker load --input "/tmp/lms-${COMMIT_SHA}.tar.gz"
docker tag "lms-service:${COMMIT_SHA}" lms-service:local

docker compose config --quiet

# Поднимаем базу и брокер, дожидаемся готовности.
docker compose up -d --wait db redis

# При ошибке миграций скрипт остановится до замены приложения.
docker compose run --rm --no-deps migrate

# Используем готовый образ, на сервере повторной сборки нет.
docker compose up -d --no-build --no-deps --force-recreate \
    web worker beat nginx

docker compose exec -T nginx nginx -t
docker compose exec -T web python manage.py check

# Дожидаемся ответа приложения через Nginx.
curl --fail --silent --show-error \
    --retry 12 --retry-delay 5 --retry-all-errors \
    --connect-timeout 5 --max-time 15 \
    http://127.0.0.1/api/docs/ \
    --output /dev/null

rm -- "/tmp/lms-${COMMIT_SHA}.tar.gz"

echo "Deployment completed: ${COMMIT_SHA}"