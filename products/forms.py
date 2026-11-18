from django import forms
from .models import FoodProduct

class ProductForm(forms.ModelForm):
    class Meta:
        model = FoodProduct
        fields = ('name','brand','calories_per_100g','protein_per_100g','fat_per_100g','carbs_per_100g','tags','is_public')
