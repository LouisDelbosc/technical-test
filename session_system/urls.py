# login_system/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Define your URL patterns here
    path('session/', views.SessionView.as_view(), name='session-create'),
]