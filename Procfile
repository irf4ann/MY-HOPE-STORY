web: gunicorn myhopestory.wsgi:application
worker: celery -A myhopestory worker -l info
beat: celery -A myhopestory beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
