web: python manage.py migrate --noinput && python manage.py create_demo_users && exec daphne -b 0.0.0.0 -p $PORT myhopestory.asgi:application
worker: celery -A myhopestory worker -l info
beat: celery -A myhopestory beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
