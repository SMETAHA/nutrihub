from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

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

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_public"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(calories_per_100g__gte=0)
                    & models.Q(protein_per_100g__gte=0)
                    & models.Q(fat_per_100g__gte=0)
                    & models.Q(carbs_per_100g__gte=0)
                    & models.Q(fiber_per_100g__gte=0)
                    & models.Q(sugar_per_100g__gte=0)
                    & models.Q(sodium_mg_per_100g__gte=0)
                    & models.Q(potassium_mg_per_100g__gte=0)
                ),
                name="food_product_nutrients_nonnegative",
            ),
        ]

    def clean(self):
        super().clean()
        if not self.name or not self.name.strip():
            raise ValidationError({"name": "Название продукта не может быть пустым."})
        fields = (
            "calories_per_100g",
            "protein_per_100g",
            "fat_per_100g",
            "carbs_per_100g",
            "fiber_per_100g",
            "sugar_per_100g",
            "sodium_mg_per_100g",
            "potassium_mg_per_100g",
        )
        for field in fields:
            value = getattr(self, field, None)
            if value is not None and value < 0:
                raise ValidationError({field: "Значение не может быть отрицательным."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class Portion(models.Model):
    product = models.ForeignKey(FoodProduct, on_delete=models.CASCADE, related_name='portions')
    name = models.CharField(max_length=64)  # «1 яйцо», «ломтик», «столовая ложка»
    grams = models.FloatField()


    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
