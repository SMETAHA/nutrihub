from django.urls import path
from . import views

urlpatterns = [
    path("", views.recipe_list, name="recipe_list"),
    path("new/", views.recipe_create, name="recipe_create"),
    path("<int:pk>/edit/", views.recipe_edit, name="recipe_edit"),
    path("<int:pk>/delete/", views.recipe_delete, name="recipe_delete"),

    path("api/products/", views.api_products_search, name="recipes_api_products"),
]
