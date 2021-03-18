from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
class UserRegistrationForms(UserCreationForm):
    class Meta:
        model=User
        fields=['email','username','password1','password2']
    def clean(self):
        email=self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        username=self.cleaned_data.get('username')
        if len(username)<6:
            raise  ValidationError("username cannot be less than 6 characters")
        return self.cleaned_data
class ChangePasswordForm(forms.Form):
    oldPassword=forms.CharField()
    newPassword=forms.CharField()
    def clean(self):
        oldPassword=self.cleaned_data.get('oldPassword')
        newPassword=self.cleaned_data.get('newPassword')
        if oldPassword==newPassword:
            raise ValidationError("Passoword cannot be same")



class GithubUrlForm(forms.Form):
    repository_url=forms.URLField(required=True)
