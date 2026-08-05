#!/usr/bin/env bash
set -e

exec gunicorn myhopestory.wsgi:application --bind 0.0.0.0:$PORT
