"""
URL mappings for the user API.
"""
from django.urls import path

from .views import CreateUserApiView

app_name = 'user'

urlpatterns = [
    path('create/', CreateUserApiView.as_view(), name='create'),
]
