from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from phonenumber_field.widgets import PhoneNumberPrefixWidget
from phonenumber_field.modelfields import PhoneNumberField

from .models import Bid, Opinion, Auction


User = get_user_model()


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']


class OpinionForm(forms.ModelForm):
    class Meta:
        model = Opinion
        fields = ['rating', 'comment']


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
    email = forms.EmailField(required=True)

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
    end_date = forms.DateTimeField(widget=forms.TextInput(attrs={'placeholder': '01/20/1995 15:30:00'}),
                                    help_text='month/day/year hour:minutes:seconds')


class EditUserForm(forms.Form):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    phone_number = forms.CharField(widget=PhoneNumberPrefixWidget(), required=False)


class EditOpinionForm(forms.ModelForm):
    class Meta:
        model = Opinion
        fields = ['rating', 'comment']
