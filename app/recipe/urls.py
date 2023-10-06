"""
URL's for recipe API's.
"""
from django.urls import (
    path,
    include
)

from rest_framework import routers

from recipe import views


router = routers.DefaultRouter()
router.register('recipes', views.RecipeApiViewSet)
router.register('tags', views.TagApiViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls)),
]
