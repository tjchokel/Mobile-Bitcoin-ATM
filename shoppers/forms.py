from django import forms
from django.forms import extras


class ShopperInformationForm(forms.Form):
    name = forms.CharField(
        required=True,
        label='Name',
        widget=forms.TextInput(attrs={'placeholder': 'John Smith'}),
        min_length=2,
    )

    email = forms.EmailField(
        label='Email Address',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )

    phone_num = forms.CharField(
        label='Phone Number',
        min_length=3,
        max_length=30,
        required=False,
        widget=forms.TextInput(),
    )