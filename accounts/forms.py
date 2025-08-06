from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        help_text="Select Student or Teacher"
    )

    class Meta:
        model = User
        fields = ("username", "email", "role", "password1", "password2")
