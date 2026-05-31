from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Pet, PlayerProfile


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class PetForm(forms.ModelForm):
    class Meta:
        model = Pet
        fields = ("name", "species")
        labels = {
            "name": "Имя питомца",
            "species": "Вид",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Например, Пуфик"}),
        }


class ProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = PlayerProfile
        fields = ("display_name", "bio")
        labels = {
            "display_name": "Отображаемое имя",
            "bio": "О себе",
        }
        widgets = {
            "display_name": forms.TextInput(attrs={"placeholder": "Как показывать имя в игре"}),
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Короткая заметка для профиля"}),
        }
