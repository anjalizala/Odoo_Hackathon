
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Question, Answer, Tag

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text='Required. Enter a valid email address.')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class QuestionForm(forms.ModelForm):
    tags = forms.CharField(help_text='Comma-separated tags')

    class Meta:
        model = Question
        fields = ['title', 'description', 'tags']

    def clean_tags(self):
        tags_str = self.cleaned_data['tags']
        tags_list = [tag.strip() for tag in tags_str.split(',')]
        return tags_list

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content']
