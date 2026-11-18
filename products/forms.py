from django import forms
from django.utils.translation import gettext_lazy as _
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
            'name': _('Name'),
            'brand': _('Brand'),
            'calories_per_100g': _('Calories per 100 g'),
            'protein_per_100g': _('Protein per 100 g'),
            'fat_per_100g': _('Fat per 100 g'),
            'carbs_per_100g': _('Carbohydrates per 100 g'),
            'fiber_per_100g': _('Fiber per 100 g'),
            'sugar_per_100g': _('Sugar per 100 g'),
            'sodium_mg_per_100g': _('Sodium per 100 g (mg)'),
            'potassium_mg_per_100g': _('Potassium per 100 g (mg)'),
            'tags': _('Tags (comma-separated)'),
            'is_public': _('Public product'),
        }
        widgets = {
            field: forms.NumberInput(attrs={'min': 0, 'step': 0.1})
            for field in (
                'calories_per_100g', 'protein_per_100g', 'fat_per_100g', 'carbs_per_100g',
                'fiber_per_100g', 'sugar_per_100g', 'sodium_mg_per_100g', 'potassium_mg_per_100g',
            )
        }
