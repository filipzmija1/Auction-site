from django import forms
from django.contrib.auth import get_user_model

from .models import Bid, Opinion


user = get_user_model()


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        exclude = ['auction']


class OpinionForm(forms.ModelForm):
    class Meta:
        model = Opinion
        fields = ['reviewer', 'rating', 'comment']


class SearchForm(forms.Form):
    search = forms.CharField(min_length=3, required=False)


class LoginForm(forms.Form):
    username = forms.CharField(max_length=64)
    password = forms.CharField(widget=forms.PasswordInput)


class AddUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = user
        fields = ['username', 'password', 'confirm_password', 'first_name', 'last_name', 'email']
