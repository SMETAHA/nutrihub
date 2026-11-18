from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text',)
        labels = {'text': _('Your post')}
        widgets = {'text': forms.Textarea(attrs={'rows': 2, 'placeholder': _('Share your progress or a recipe...')})}
