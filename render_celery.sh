#!/usr/bin/env bash
set -e

exec celery -A myhopestory worker -l info
