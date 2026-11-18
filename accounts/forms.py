from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, SEX_CHOICES, ACTIVITY_CHOICES, GOAL_CHOICES, THEME_CHOICES

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            'bio', 'avatar', 'sex', 'birth_date',
            'height_cm', 'start_weight_kg', 'current_weight_kg', 'target_weight_kg',
            'waist_cm', 'neck_cm', 'hip_cm', 'body_fat_percent',
            'activity_level', 'goal_type', 'weekly_delta_kg',
            'macro_mode', 'theme'
        )
        widgets = {
            'birth_date': forms.DateInput(attrs={'type':'date'}),
        }
        help_texts = {
            'waist_cm': 'Измерьте по самой узкой части живота',
            'neck_cm': 'Измерьте по основанию шеи',
            'hip_cm': 'Измерьте по самым широким бёдрам (для женщин)',
            'body_fat_percent': 'Если известен — введите для точного расчёта BMR',
        }
