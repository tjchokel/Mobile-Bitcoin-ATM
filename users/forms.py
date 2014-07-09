from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _
from countries import COUNTRY_DROPDOWN


class CustomerRegistrationForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )
    city = forms.CharField(
        label=_('City'),
        required=False,
    )
    country = forms.ChoiceField(
        label=_('Country'),
        required=True,
        choices=COUNTRY_DROPDOWN,
        widget=forms.Select(attrs={'data-country': 'USA'}),
    )
    intention = forms.ChoiceField(
        label=_('Which service interests you the most?'),
        required=False,
        widget=forms.RadioSelect(),
        choices=(
            ('buy_btc', 'Spend Cash to Buy Bitcoin'),
            ('sell_btc', 'Sell Bitcoin to Receive Cash'),
        ),
    )


class ContactForm(forms.Form):
    email = forms.EmailField(
        label=_('Your Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )
    name = forms.CharField(
        label=_('Name'),
        required=True,
    )
    message = forms.CharField(
        label=_('Message'),
        required=True,
        widget=forms.Textarea(),
    )