from django.urls import path
from .views import story_wizard_view

urlpatterns = [
    path('share/', story_wizard_view, name='story_wizard'),
]
