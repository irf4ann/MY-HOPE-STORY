from django.urls import path

from .views import mentors_view

urlpatterns = [
    path('', mentors_view, name='mentors'),
]
