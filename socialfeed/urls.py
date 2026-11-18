from django.urls import path
from .views import feed, add_friend, react

urlpatterns = [
    path('', feed, name='feed'),
    path('add-friend/<str:username>/', add_friend, name='add_friend'),
    path('react/<int:post_id>/<str:kind>/', react, name='react'),
]
