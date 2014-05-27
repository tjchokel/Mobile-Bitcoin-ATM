from django import forms
from django.forms import extras
from countries import COUNTRY_DROPDOWN


class LoginForm(forms.Form):
    username = forms.CharField(required=True)
    password = forms.CharField(required=True,
        widget=forms.PasswordInput(render_value=False))


class AccountRegistrationForm(forms.Form):
    email = forms.EmailField(
        label='Email Address',
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )

    password = forms.CharField(
        required=True,
        label='Secure Password',
        widget=forms.PasswordInput(attrs={'id': 'pass1'}),
        min_length=6,
    )

    password_confirm = forms.CharField(
        required=True,
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'id': 'pass2'}),
        min_length=6
    )


class PersonalInfoRegistrationForm(forms.Form):
    first_name = forms.CharField(
        label='First Name',
        required=True,
        min_length=2,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': 'John'}),
    )

    last_name = forms.CharField(
        label='Last Name',
        required=True,
        min_length=2,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': 'Smith'}),
    )

    phone_num = forms.CharField(
        label='Cell Phone Number in International Format',
        min_length=10,
        required=True,
        widget=forms.TextInput(attrs={'class': 'bfh-phone', 'data-country': 'id_phone_country'}),
    )

class BusinessInfoRegistrationForm(forms.Form):

    business_name = forms.CharField(
        label='Store Name',
        required=True,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': "Mel's Diner"}),
    )

    address_1 = forms.CharField(
        label='Address Line 1',
        min_length=5,
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Street address, P.O. box, company name, c/o '}),
    )

    address_2 = forms.CharField(
        label='Address Line 2',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Apartment, suite, unit, building, floor, etc.'}),
    )

    city = forms.CharField(
        label='City',
        required=True,
        max_length=30,
        widget=forms.TextInput(),
    )
    state = forms.CharField(
        label='State/Province/Region',
        required=True,
        min_length=2,
        max_length=30,
        widget=forms.TextInput(),
    )

    zip_code = forms.CharField(
        label='Zip Code',
        min_length=3,
        max_length=30,
        required=True,
        widget=forms.TextInput(),
    )
    country = forms.ChoiceField(
        required=True,
        choices=COUNTRY_DROPDOWN,
        widget=forms.Select(attrs={'data-country': 'USA'}),
    )
    zip_code = forms.CharField(
        label='Zip Code',
        min_length=3,
        max_length=30,
        required=True,
        widget=forms.TextInput(),
    )

    phone_num = forms.CharField(
        label='Phone Number',
        min_length=3,
        max_length=30,
        required=True,
        widget=forms.TextInput(),
    )

    hours = forms.CharField(
        label='Hours',
        min_length=3,
        max_length=30,
        required=True,
        widget=forms.TextInput(),
    )

    currency_code = forms.CharField(
        label='Currency',
        min_length=3,
        max_length=30,
        required=True,
        widget=forms.TextInput(),
    )
