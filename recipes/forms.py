# recipes/forms.py
from django import forms
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Recipe, RecipeIngredient
from products.models import FoodProduct

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ("name", "servings", "instructions", "image", "tags", "is_public")
        labels = {
            "name": _("Name"),
            "servings": _("Servings"),
            "instructions": _("Instructions"),
            "image": _("Photo"),
            "tags": _("Tags (comma-separated)"),
            "is_public": _("Public recipe"),
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Recipe name")}),
            "servings": forms.NumberInput(attrs={"min": "0.1", "step": "0.1"}),
            "instructions": forms.Textarea(attrs={"rows": 5, "placeholder": _("Describe the cooking steps")}),
            "tags": forms.TextInput(attrs={"placeholder": _("e.g. breakfast, pasta")}),
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
