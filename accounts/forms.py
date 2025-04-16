from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "initials", "first_name", "last_name", "party")


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['initials', 'first_name', 'last_name', 'email', 'party']
