from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from products.models import FoodProduct

class Recipe(models.Model):
    name = models.CharField("Название", max_length=200)
    servings = models.FloatField("Порций", default=1)
    instructions = models.TextField("Инструкции", blank=True)
    image = models.ImageField("Фото", upload_to="recipes/", blank=True, null=True)
    tags = models.CharField("Теги (через запятую)", max_length=200, blank=True)
    is_public = models.BooleanField("Публичный", default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.name or f"Рецепт #{self.pk}"

    @property
    def total_weight(self):
        """Общий вес всех ингредиентов в рецепте."""
        return sum(ing.grams for ing in self.ingredients.all())

    @property
    def total_kcal(self):
        """Общая калорийность рецепта (на весь рецепт)."""
        return sum(
            (ing.grams / 100) * ing.product.calories_per_100g
            for ing in self.ingredients.all()
        )

    @property
    def kcal_per_serving(self):
        """Калорийность на 1 порцию."""
        if self.servings > 0:
            return self.total_kcal / self.servings
        return self.total_kcal

    # — агрегаты по ингредиентам —
    @property
    def total_grams(self) -> float:
        return sum(ing.grams for ing in self.ingredients.all())

    @property
    def total_kcall(self) -> float:
        return sum(ing.kcal for ing in self.ingredients.all())

    @property
    def total_protein(self) -> float:
        return sum(ing.protein for ing in self.ingredients.all())

    @property
    def total_fat(self) -> float:
        return sum(ing.fat for ing in self.ingredients.all())

    @property
    def total_carbs(self) -> float:
        return sum(ing.carbs for ing in self.ingredients.all())

    @property
    def per_serving_kcal(self) -> float:
        return self.total_kcal / self.servings if self.servings else 0

    @property
    def per100_kcal(self) -> float:
        g = self.total_grams or 0
        return (self.total_kcal / g * 100) if g else 0


class RecipeIngredient(models.Model):
    class Unit(models.TextChoices):
        GRAM = "g", "г"
        ML   = "ml", "мл"
        PCS  = "pcs", "шт"

    recipe = models.ForeignKey(Recipe, related_name="ingredients", on_delete=models.CASCADE)
    product = models.ForeignKey(FoodProduct, on_delete=models.PROTECT, verbose_name="Продукт")
    amount = models.FloatField("Кол-во", default=0)      # то, что вводит пользователь
    unit = models.CharField("Ед.", max_length=8, choices=Unit.choices, default=Unit.GRAM)
    piece_grams = models.FloatField("Вес 1 шт (г)", default=0, help_text="Для ед. 'шт'")
    weight = models.FloatField(null=True, blank=True, default=0)


    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"

    def __str__(self):
        return f"{self.product} — {self.amount} {self.unit}"

    @property
    def grams(self) -> float:
        if self.unit == self.Unit.GRAM:
            return self.amount
        if self.unit == self.Unit.ML:
            # упрощение: считаем 1 мл ≈ 1 г
            return self.amount
        if self.unit == self.Unit.PCS:
            return (self.piece_grams or 0) * (self.amount or 0)
        return 0.0

    # — расчёт БЖУ/ккал на основе FoodProduct per100 —
    def _scale(self, per100: float) -> float:
        return (per100 or 0) * self.grams / 100.0

    @property
    def kcal(self) -> float:
        return self._scale(self.product.calories_per_100g)

    @property
    def protein(self) -> float:
        return self._scale(self.product.protein_per_100g)

    @property
    def fat(self) -> float:
        return self._scale(self.product.fat_per_100g)

    @property
    def carbs(self) -> float:
        return self._scale(self.product.carbs_per_100g)