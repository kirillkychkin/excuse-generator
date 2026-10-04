#!/bin/sh
# Перед запуском приложения применяем миграции и заполняем справочники.
set -e

alembic upgrade head
python -m app.seed

# --proxy-headers: за HTTPS-прокси хостинга ссылки на статику строятся с https://
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --proxy-headers \
    --forwarded-allow-ips="*"
