from django import forms
from .models import FoodProduct

class ProductForm(forms.ModelForm):
    class Meta:
        model = FoodProduct
        fields = (
            'name', 'brand',
            'calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g',
            'fiber_per_100g', 'sugar_per_100g', 'sodium_mg_per_100g', 'potassium_mg_per_100g',
            'tags', 'is_public',
        )
        labels = {
            'name': 'Название',
            'brand': 'Бренд',
            'calories_per_100g': 'Ккал на 100 г',
            'protein_per_100g': 'Белки на 100 г',
            'fat_per_100g': 'Жиры на 100 г',
            'carbs_per_100g': 'Углеводы на 100 г',
            'fiber_per_100g': 'Клетчатка на 100 г',
            'sugar_per_100g': 'Сахар на 100 г',
            'sodium_mg_per_100g': 'Натрий на 100 г, мг',
            'potassium_mg_per_100g': 'Калий на 100 г, мг',
            'tags': 'Теги через запятую',
            'is_public': 'Публичный продукт',
        }
        widgets = {
            field: forms.NumberInput(attrs={'min': 0, 'step': 0.1})
            for field in (
                'calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g',
                'fiber_per_100g', 'sugar_per_100g', 'sodium_mg_per_100g', 'potassium_mg_per_100g',
            )
        }
