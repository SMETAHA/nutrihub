from django.urls import path
from .views import product_list, product_create, quick_add_to_diary,add_product,api_search_products

urlpatterns = [
    path('', product_list, name='product_list'),
    path('new/', product_create, name='product_create'),

    path('add/', add_product, name='add_product'),
    path('api/search/', api_search_products, name='products_api_search'),

    path('add/<int:pk>/', quick_add_to_diary, name='product_quick_add'),
]

