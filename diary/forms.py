from django import forms
from .models import DiaryEntry, WeightLog

class DiaryEntryForm(forms.ModelForm):
    class Meta:
        model = DiaryEntry
        fields = ['time', 'product', 'recipe', 'grams']
        widgets = {
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'grams': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }
        labels = {
            'time': 'Время приёма пищи',
            'product': 'Продукт',
            'recipe': 'Блюдо',
            'grams': 'Вес (г)',
        }

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        recipe = cleaned_data.get('recipe')
        if not product and not recipe:
            raise forms.ValidationError("Выберите либо продукт, либо блюдо.")
        if product and recipe:
            raise forms.ValidationError("Нельзя выбрать и продукт, и блюдо одновременно.")
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
            'date': 'Дата',
            'weight': 'Вес (кг)',
        }
