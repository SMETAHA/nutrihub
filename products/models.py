from django.db import models
from django.contrib.auth.models import User

class FoodProduct(models.Model):
    name = models.CharField(max_length=120)
    brand = models.CharField(max_length=120, blank=True)
    calories_per_100g = models.FloatField()
    protein_per_100g = models.FloatField(default=0)
    fat_per_100g = models.FloatField(default=0)
    carbs_per_100g = models.FloatField(default=0)
    fiber_per_100g = models.FloatField(default=0)     # NEW
    sugar_per_100g = models.FloatField(default=0)     # NEW
    sodium_mg_per_100g = models.FloatField(default=0) # NEW
    potassium_mg_per_100g = models.FloatField(default=0) # NEW
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    tags = models.CharField(max_length=200, blank=True)

class Portion(models.Model):
    product = models.ForeignKey(FoodProduct, on_delete=models.CASCADE, related_name='portions')
    name = models.CharField(max_length=64)  # «1 яйцо», «ломтик», «столовая ложка»
    grams = models.FloatField()


    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
