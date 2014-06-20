from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from countries import COUNTRY_DROPDOWN

from utils import clean_phone_num

class ShopperInformationForm(forms.Form):
    name = forms.CharField(
        required=True,
        label=_('Name'),
        widget=forms.TextInput(attrs={'placeholder': 'John Smith'}),
        min_length=2,
    )

    email = forms.EmailField(
        label=_('Email'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )

    phone_country = forms.ChoiceField(
            label=_('Phone Country'),
            required=False,
            choices=COUNTRY_DROPDOWN,
            widget=forms.Select(attrs={'data-country': 'USA'}),
    )

    phone_num = forms.CharField(
            label=_('Cell Phone Number in International Format'),
            required=False,
            widget=forms.TextInput(attrs={'class': 'bfh-phone', 'data-country': 'id_phone_country'}),
    )

    clean_phone_num = clean_phone_num


class BuyBitcoinForm(forms.Form):
    amount = forms.DecimalField(
            label=_('Fiat Amount'),
            required=True,
            validators=[MinValueValidator(0.0), MaxValueValidator(1000.0)],
            help_text=_('The amount of cash you will be handing to the merchant'),
            widget=forms.TextInput(attrs={'class': 'needs-input-group'}),
    )

    email = forms.CharField(
        label=_('Email'),
        required=True,
        widget=forms.TextInput(attrs={'id': 'email-field', 'placeholder': 'me@example.com'}),
    )
    
    email_or_btc_address = forms.ChoiceField(
        label=_('Send to Email or Bitcoin Address'),
        required=True,
        widget=forms.RadioSelect(attrs={'id': 'address'}),
        choices=(('1', 'Email Address',), ('2', 'Bitcoin Address',)),
    )

    btc_address = forms.CharField(
            label=_('Bitcoin Deposit Address'),
            required=False,
            min_length=27,
            max_length=34,
            help_text=_('The wallet address where you want your bitcoin sent (optional)'),
            widget=forms.TextInput(),
    )


class ConfirmPasswordForm(forms.Form):
    password = forms.CharField(
            required=True,
            label='Verify Merchant Password',
            widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            print 'VALIDATION ERROR'
            raise forms.ValidationError('Invalid password')


    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ConfirmPasswordForm, self).__init__(*args, **kwargs)