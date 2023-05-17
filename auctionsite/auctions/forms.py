from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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
    phone_number = forms.CharField(required=False, help_text='This field is used to receive SMS when you will be outbid')

    def clean_phone_number(self, *args, **kwargs):
        phone_number = self.cleaned_data.get('phone_number')
        for number in phone_number:
            try:
                int(number)
            except:
                raise forms.ValidationError('Phone number must contains only numbers!')
        if len(phone_number) != 9:
            raise forms.ValidationError('Phone number must have 9 numbers')
        else:
            return phone_number

class EditOpinionForm(forms.ModelForm):
    class Meta:
        model = Opinion
        fields = ['rating', 'comment']
