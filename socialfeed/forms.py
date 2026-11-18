from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text',)
        widgets = {'text': forms.Textarea(attrs={'rows':2,'placeholder':'Поделитесь прогрессом или рецептом...'})}
