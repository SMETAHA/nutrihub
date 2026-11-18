from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from .views import (
    DiaryEntryViewSet,
    FoodProductViewSet,
    PlannedMealViewSet,
    RecipeViewSet,
)

router = DefaultRouter()
router.register('products', FoodProductViewSet, basename='api-product')
router.register('recipes', RecipeViewSet, basename='api-recipe')
router.register('diary', DiaryEntryViewSet, basename='api-diary')
router.register('planned-meals', PlannedMealViewSet, basename='api-planned-meal')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', obtain_auth_token, name='api-token'),
]
