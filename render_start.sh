#!/usr/bin/env bash
set -e

exec daphne -b 0.0.0.0 -p $PORT myhopestory.asgi:application

