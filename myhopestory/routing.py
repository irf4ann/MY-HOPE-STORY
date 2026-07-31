"""
Django Channels routing configuration.
Defines WebSocket URL patterns and consumers.
"""

from django.urls import path, re_path
from notifications.consumers import NotificationConsumer, ChatConsumer

# WebSocket URL routing
websocket_urlpatterns = [
    # Notifications WebSocket
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    
    # Chat WebSocket
    re_path(r'ws/chat/(?P<chat_id>\d+)/$', ChatConsumer.as_asgi()),
]
