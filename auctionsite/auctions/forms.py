from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from .models import Bid, Opinion, Auction


User = get_user_model()


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
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'confirm_password', 'email']


class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)


class AddAuctionForm(forms.ModelForm):
    class Meta:
        model = Auction
        fields = ['name', 'item', 'min_price', 'buy_now_price', 'end_date']
