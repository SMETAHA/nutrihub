from datetime import date, time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from products.models import FoodProduct
from recipes.models import Recipe

MEAL_CHOICES = [
    ("breakfast","Завтрак"),
    ("lunch","Обед"),
    ("dinner","Ужин"),
    ("snack","Перекус"),
]

class DiaryEntry(models.Model):
    user  = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    date  = models.DateField(default=date.today)
    time  = models.TimeField(default=time(hour=12))
    meal  = models.CharField(max_length=16, choices=MEAL_CHOICES, default="breakfast")

    # либо продукт, либо рецепт (ровно один)
    product = models.ForeignKey(FoodProduct, null=True, blank=True, on_delete=models.CASCADE)
    recipe  = models.ForeignKey(Recipe, null=True, blank=True, on_delete=models.CASCADE)

    grams     = models.FloatField(default=0)   # для продукта ИЛИ рецепт-в-граммах
    servings  = models.FloatField(default=0)   # для рецепта "в порциях"
    note      = models.CharField(max_length=240, blank=True)

    # храним посчитанные итоги для истории
    total_kcal    = models.FloatField(default=0)
    total_protein = models.FloatField(default=0)
    total_fat     = models.FloatField(default=0)
    total_carbs   = models.FloatField(default=0)

    class Meta:
        ordering = ["-date","-time"]
        indexes = [models.Index(fields=["user","date"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(product__isnull=False, recipe__isnull=True)
                    | models.Q(product__isnull=True, recipe__isnull=False)
                ),
                name="diary_entry_exactly_one_source",
            ),
        ]

    def clean(self):
        # простая валидация: выбран один источник
        if bool(self.product) == bool(self.recipe):
            raise ValidationError("Нужно выбрать либо продукт, либо блюдо (рецепт).")
        if self.grams < 0 or self.servings < 0:
            raise ValidationError("Вес и количество порций не могут быть отрицательными.")

    def _calc_from_product(self):
        g = max(self.grams, 0.0)
        self.total_kcal    = self.product.calories_per_100g    * g / 100.0
        self.total_protein = self.product.protein_per_100g * g / 100.0
        self.total_fat     = self.product.fat_per_100g     * g / 100.0
        self.total_carbs   = self.product.carbs_per_100g   * g / 100.0

    def _calc_from_recipe_by_servings(self):
        s = max(self.servings, 0.0)
        base = max(self.recipe.servings, 1e-9)
        self.total_kcal    = self.recipe.total_kcal    * s / base
        self.total_protein = self.recipe.total_protein * s / base
        self.total_fat     = self.recipe.total_fat     * s / base
        self.total_carbs   = self.recipe.total_carbs   * s / base

    def _calc_from_recipe_by_grams(self):
        g = max(self.grams, 0.0)
        tw = max(self.recipe.total_weight, 1e-9)
        self.total_kcal    = self.recipe.total_kcal    * g / tw
        self.total_protein = self.recipe.total_protein * g / tw
        self.total_fat     = self.recipe.total_fat     * g / tw
        self.total_carbs   = self.recipe.total_carbs   * g / tw

    def save(self, *args, **kwargs):
        self.full_clean()
        # авторасчёт перед сохранением
        if self.product:
            self._calc_from_product()
        elif self.recipe:
            if self.servings > 0:
                self._calc_from_recipe_by_servings()
            else:
                self._calc_from_recipe_by_grams()
        super().save(*args, **kwargs)

class WeightLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weight_logs')
    date = models.DateField()
    weight = models.FloatField()

    class Meta:
        ordering = ['-date']
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} — {self.weight} кг ({self.date})"




class PlannedMeal(models.Model):
    MEAL_TYPES = [
        ('breakfast', 'Завтрак'),
        ('lunch', 'Обед'),
        ('dinner', 'Ужин'),
        ('snack', 'Перекус'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES)
    product = models.ForeignKey(FoodProduct, on_delete=models.SET_NULL, null=True, blank=True)
    recipe = models.ForeignKey(Recipe, on_delete=models.SET_NULL, null=True, blank=True)
    grams = models.FloatField(default=0)
    servings = models.FloatField(default=0)
    note = models.CharField(max_length=255, blank=True)
    done = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'time']
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(product__isnull=False, recipe__isnull=True)
                    | models.Q(product__isnull=True, recipe__isnull=False)
                ),
                name="planned_meal_exactly_one_source",
            ),
        ]

    def clean(self):
        if bool(self.product) == bool(self.recipe):
            raise ValidationError("Нужно выбрать либо продукт, либо блюдо (рецепт).")
        if self.grams < 0 or self.servings < 0:
            raise ValidationError("Вес и количество порций не могут быть отрицательными.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} — {self.date} {self.meal_type}"

    @property
    def name(self):
        return self.product.name if self.product else (self.recipe.name if self.recipe else "—")

    @property
    def kcal(self):
        if self.product:
            return (self.product.calories_per_100g * self.grams) / 100
        elif self.recipe:
            total = self.recipe.total_kcal
            if self.servings:
                return total / max(self.recipe.servings, 1) * self.servings
            elif self.grams:
                return total / max(self.recipe.total_weight, 1) * self.grams
        return 0

# 📊 те же свойства, что и у DiaryEntry
    @property
    def total_kcal(self):
        if self.product:
            return self.grams * (self.product.calories_per_100g or 0) / 100
        if self.recipe:
            return self.servings * (self.recipe.per_serving_kcal or 0)
        return 0

    @property
    def total_protein(self):
        if self.product:
            return self.grams * (self.product.protein_per_100g or 0) / 100
        if self.recipe:
            return self.servings * (self.recipe.total_protein / self.recipe.servings)
        return 0

    @property
    def total_fat(self):
        if self.product:
            return self.grams * (self.product.fat_per_100g or 0) / 100
        if self.recipe:
            return self.servings * (self.recipe.total_fat / self.recipe.servings)
        return 0

    @property
    def total_carbs(self):
        if self.product:
            return self.grams * (self.product.carbs_per_100g or 0) / 100
        if self.recipe:
            return self.servings * (self.recipe.total_carbs / self.recipe.servings)
        return 0