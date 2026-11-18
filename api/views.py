from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from diary.models import DiaryEntry, PlannedMeal
from products.models import FoodProduct
from recipes.models import Recipe
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    DiaryEntrySerializer,
    FoodProductSerializer,
    PlannedMealSerializer,
    RecipeSerializer,
)


class FoodProductViewSet(viewsets.ModelViewSet):
    serializer_class = FoodProductSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = FoodProduct.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            )
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset.select_related('created_by').order_by('name')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            )
        return queryset.select_related('created_by').prefetch_related(
            'ingredients__product'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DiaryEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DiaryEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DiaryEntry.objects.filter(
            user=self.request.user
        ).select_related('product', 'recipe').order_by('-date', '-time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PlannedMealViewSet(viewsets.ModelViewSet):
    serializer_class = PlannedMealSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PlannedMeal.objects.filter(
            user=self.request.user
        ).select_related('product', 'recipe').order_by('date', 'time')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
