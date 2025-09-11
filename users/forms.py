from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile

class CustomUserCreationForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True)
    country = forms.CharField(max_length=64, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'name', 'email', 'country', 'password1', 'password2')

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise forms.ValidationError('Email is required')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email already registered')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').strip().lower()
        user.first_name = (self.cleaned_data.get('name') or '').strip()
        if commit:
            user.save()
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.country = (self.cleaned_data.get('country') or '').strip()
            profile.save()
        return user