"""
URL's for recipe API's.
"""
from django.urls import (
    path,
    include
)

from rest_framework import routers

from .views import RecipeApiViewSet


router = routers.DefaultRouter()
router.register('recipes', RecipeApiViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
