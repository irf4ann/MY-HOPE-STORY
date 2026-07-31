from django.contrib.auth import views as auth_views
from django.urls import path

from .views import profile_view, signup_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('profile/', profile_view, name='profile'),
]
