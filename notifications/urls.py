from django.urls import path

from .views import notifications_inbox_view

urlpatterns = [
    path('', notifications_inbox_view, name='notifications_inbox'),
]
