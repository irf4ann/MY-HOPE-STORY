#!/usr/bin/env bash
set -e

echo "===> Running Database Migrations..."
python manage.py migrate --noinput

echo "===> Creating Demo Users..."
python manage.py create_demo_users || true

echo "===> Starting Daphne Application Server..."
exec daphne -b 0.0.0.0 -p $PORT myhopestory.asgi:application


