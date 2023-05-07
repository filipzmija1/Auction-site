from django import forms

from .models import Bid, Opinion


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

