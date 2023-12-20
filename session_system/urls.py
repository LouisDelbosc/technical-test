# login_system/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Define your URL patterns here
    path('session/', views.create_session, name='session-create'),
    path('session/<str:prefixed_uuid>/', views.update_session, name='update-session'),
]