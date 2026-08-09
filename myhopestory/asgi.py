"""
ASGI config for myhopestory project with Django Channels support.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myhopestory.settings')

# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Run automatic database migrations & seed users on server start
try:
    from django.core.management import call_command
    call_command('migrate', interactive=False)
    call_command('create_demo_users')
except Exception as e:
    print(f"Startup migration status: {e}")

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from myhopestory.routing import websocket_urlpatterns

# ASGI application with Channels support
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
