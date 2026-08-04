from django.urls import path

from .views import checkout_session_view

urlpatterns = [
    path('checkout/<int:story_id>/', checkout_session_view, name='checkout_session'),
]
