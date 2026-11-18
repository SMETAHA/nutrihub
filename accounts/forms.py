from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
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
        labels = {
            'bio': _('About you'),
            'avatar': _('Avatar'),
            'sex': _('Sex'),
            'birth_date': _('Date of birth'),
            'height_cm': _('Height (cm)'),
            'start_weight_kg': _('Starting weight (kg)'),
            'current_weight_kg': _('Current weight (kg)'),
            'target_weight_kg': _('Target weight (kg)'),
            'waist_cm': _('Waist (cm)'),
            'neck_cm': _('Neck (cm)'),
            'hip_cm': _('Hips (cm)'),
            'body_fat_percent': _('Body fat (%)'),
            'activity_level': _('Activity level'),
            'goal_type': _('Goal'),
            'weekly_delta_kg': _('Weekly change (kg)'),
            'macro_mode': _('Macro mode'),
            'theme': _('Interface theme'),
        }
        help_texts = {
            'waist_cm': _('Measure around the narrowest part of your waist.'),
            'neck_cm': _('Measure at the base of your neck.'),
            'hip_cm': _('Measure around the widest part of your hips.'),
            'body_fat_percent': _('Enter if known to improve BMR estimates.'),
        }
