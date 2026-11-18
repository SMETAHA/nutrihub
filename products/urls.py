from django.urls import path
from .views import (
    product_list,
    product_create,
    product_edit,
    product_delete,
    add_product,
    quick_add_to_diary,
    api_search_products,
)

urlpatterns = [
    path('', product_list, name='product_list'),
    path('new/', product_create, name='product_create'),
    path('<int:pk>/edit/', product_edit, name='product_edit'),
    path('<int:pk>/delete/', product_delete, name='product_delete'),
    path('add/', add_product, name='add_product'),
    path('api/search/', api_search_products, name='products_api_search'),

    path('add/<int:pk>/', quick_add_to_diary, name='product_quick_add'),
]

