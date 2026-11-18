# recipes/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Recipe, RecipeIngredient
from products.models import FoodProduct

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ("name", "servings", "instructions", "image", "tags", "is_public")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Название"}),
            "servings": forms.NumberInput(attrs={"min": "0.1", "step": "0.1"}),
            "instructions": forms.Textarea(attrs={"rows": 5, "placeholder": "Опишите процесс"}),
            "tags": forms.TextInput(attrs={"placeholder": "например: завтрак, паста"}),
        }

class IngredientForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=FoodProduct.objects.all(),
        widget=forms.Select(attrs={"class": "ing-product"})
    )

    class Meta:
        model = RecipeIngredient
        fields = ("product", "amount", "unit", "piece_grams")
        widgets = {
            "amount": forms.NumberInput(attrs={"min": "0", "step": "0.1", "class": "ing-amount"}),
            "unit": forms.Select(attrs={"class": "ing-unit"}),
            "piece_grams": forms.NumberInput(attrs={"min": "0", "step": "1", "class": "ing-piece"}),
        }

IngredientFormSet = inlineformset_factory(
    Recipe,
    RecipeIngredient,
    form=IngredientForm,
    extra=1,
    can_delete=True
)
