from django.urls import path

from .views import investors_view

urlpatterns = [
    path('', investors_view, name='investors'),
]
