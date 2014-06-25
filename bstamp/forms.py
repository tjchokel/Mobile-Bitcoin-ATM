from django import forms
from django.utils.translation import ugettext_lazy as _


class BitstampAPIForm(forms.Form):

    secret_key = forms.CharField(
        label=_('Username'),
        min_length=4,
        max_length=50,
        required=True,
        widget=forms.TextInput(),
    )

    api_key = forms.CharField(
        label=_('API Key'),
        required=True,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(),
    )

    secret_key = forms.CharField(
        label=_('Secret Key'),
        min_length=5,
        max_length=50,
        required=True,
        widget=forms.TextInput(),
    )