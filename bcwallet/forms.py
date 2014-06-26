from django import forms
from django.utils.translation import ugettext_lazy as _


class BlockchainAPIForm(forms.Form):

    username = forms.CharField(
        label=_('Username'),
        required=True,
        min_length=2,
        max_length=256,
        widget=forms.TextInput(),
    )

    main_password = forms.CharField(
        label=_('Main Password'),
        min_length=4,
        max_length=50,
        required=True,
        widget=forms.PasswordInput(render_value=False),
    )

    second_password = forms.CharField(
        label=_('Second Password'),
        min_length=4,
        max_length=50,
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )