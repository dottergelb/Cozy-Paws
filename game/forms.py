from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ChatMessage, Pet, PlayerProfile, PrivateMessage, SupportTicket, UserReport


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


class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ("body",)
        labels = {"body": "Сообщение"}
        widgets = {"body": forms.TextInput(attrs={"maxlength": 240, "placeholder": "Короткое сообщение"})}


class PrivateMessageForm(forms.ModelForm):
    class Meta:
        model = PrivateMessage
        fields = ("body",)
        labels = {"body": "Сообщение"}
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "maxlength": 500, "placeholder": "Текст сообщения"})}


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ("subject", "body")
        labels = {"subject": "Тема", "body": "Описание"}
        widgets = {
            "subject": forms.TextInput(attrs={"maxlength": 120}),
            "body": forms.Textarea(attrs={"rows": 4, "maxlength": 1000}),
        }


class UserReportForm(forms.ModelForm):
    class Meta:
        model = UserReport
        fields = ("reason",)
        labels = {"reason": "Причина"}
        widgets = {"reason": forms.Textarea(attrs={"rows": 3, "maxlength": 240})}
