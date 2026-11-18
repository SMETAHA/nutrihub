from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from core.utils import bmr_mifflin, tdee, daily_target_kcal, age_from_birthdate

SEX_CHOICES = [('male', _('Male')), ('female', _('Female'))]
ACTIVITY_CHOICES = [
    ('sedentary', _('Sedentary')),
    ('light', _('Light')),
    ('moderate', _('Moderate')),
    ('active', _('Active')),
    ('very_active', _('Very active')),
]
GOAL_CHOICES = [('lose', _('Lose weight')), ('maintain', _('Maintain weight')), ('gain', _('Gain weight'))]
THEME_CHOICES = [('auto', _('Automatic')), ('light', _('Light')), ('dark', _('Dark'))]

def avatar_upload_to(instance, filename):  # simple unique path
    return f'avatars/user_{instance.user_id}/{filename}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=140, blank=True)
    avatar = models.ImageField(upload_to=avatar_upload_to, blank=True, null=True)

    # Metrics
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    height_cm = models.PositiveIntegerField(blank=True, null=True)
    start_weight_kg = models.FloatField(blank=True, null=True)
    current_weight_kg = models.FloatField(blank=True, null=True)
    target_weight_kg = models.FloatField(blank=True, null=True)
    # accounts/models.py (внутрь Profile)
    body_fat_percent = models.FloatField(blank=True, null=True)  # % жира
    neck_cm = models.FloatField(blank=True, null=True)
    waist_cm = models.FloatField(blank=True, null=True)
    hip_cm = models.FloatField(blank=True, null=True)
    MACRO_MODE_CHOICES = [('default', _('Standard')), ('athlete', _('Athlete'))]
    macro_mode = models.CharField(max_length=16, default='default')  # default|athlete

    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='light')
    goal_type = models.CharField(max_length=12, choices=GOAL_CHOICES, default='maintain')
    weekly_delta_kg = models.FloatField(default=0.5)

    theme = models.CharField(max_length=5, choices=THEME_CHOICES, default='auto')

    def age(self):
        return age_from_birthdate(self.birth_date)

    def bmr(self):
        return bmr_mifflin(self.sex, self.current_weight_kg or self.start_weight_kg, self.height_cm, self.age() or 25)

    def tdee(self):
        return tdee(self.bmr(), self.activity_level)

    def tdee_target(self):
        return daily_target_kcal(self.tdee(), self.goal_type, self.weekly_delta_kg)

    def __str__(self):
        return f'Profile({self.user.username})'

    def lean_mass(self):
        from core.utils import lean_body_mass, estimate_bf_navy
        bf = self.body_fat_percent
        if bf is None and self.sex and self.waist_cm and self.neck_cm and self.height_cm:
            bf = estimate_bf_navy(
                self.sex, self.waist_cm, self.neck_cm,
                self.hip_cm if self.sex == 'female' else None, self.height_cm
            )
        return lean_body_mass(self.current_weight_kg or self.start_weight_kg, bf) if bf is not None else None
