from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DiaryEntry, WeightLog

class DiaryEntryForm(forms.ModelForm):
    class Meta:
        model = DiaryEntry
        fields = ['time', 'meal', 'product', 'recipe', 'grams', 'servings', 'note']
        widgets = {
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'meal': forms.Select(),
            'grams': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'servings': forms.NumberInput(attrs={'min': 0, 'step': '0.1'}),
        }
        labels = {
            'time': _('Meal time'),
            'product': _('Product'),
            'recipe': _('Recipe'),
            'grams': _('Weight (g)'),
            'servings': _('Servings'),
            'note': _('Note'),
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        recipe = cleaned_data.get('recipe')
        if not product and not recipe:
            raise forms.ValidationError(_("Select either a product or a recipe."))
        if product and recipe:
            raise forms.ValidationError(_("Select a product or a recipe, not both."))
        return cleaned_data


class WeightLogForm(forms.ModelForm):
    class Meta:
        model = WeightLog
        fields = ['date', 'weight']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'weight': forms.NumberInput(attrs={'step': '0.1', 'min': '0'}),
        }
        labels = {
            'date': _('Date'),
            'weight': _('Weight (kg)'),
        }
