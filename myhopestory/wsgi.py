"""
WSGI config for myhopestory project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhopestory.settings')

application = get_wsgi_application()

# Run automatic database migrations & seed users on server start
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    call_command('create_demo_users')
except Exception as e:
    print(f"Startup migration status: {e}")
