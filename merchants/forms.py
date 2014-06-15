from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _

from bitcoins.BCAddressField import is_valid_btc_address
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from annoying.functions import get_object_or_None

from countries import COUNTRY_DROPDOWN, BFH_CURRENCY_DROPDOWN

from utils import clean_phone_num


class LoginForm(forms.Form):
    email = forms.CharField(
        label=_('Email'),
        required=True
    )
    password = forms.CharField(
        label=_('Password'),
        required=True,
        widget=forms.PasswordInput(render_value=False)
    )


class MerchantRegistrationForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )
    password = forms.CharField(
        required=True,
        label=_('Secure Password'),
        widget=forms.PasswordInput(),
        min_length=7,
    )
    full_name = forms.CharField(
        label=_('Your Name'),
        required=True,
        min_length=2,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': 'John Smith'}),
    )
    business_name = forms.CharField(
        label=_('Business Name'),
        required=True,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': "Mel's Diner"}),
    )
    country = forms.ChoiceField(
        label=_('Country'),
        required=True,
        choices=COUNTRY_DROPDOWN,
        widget=forms.Select(attrs={'data-country': 'USA'}),
    )

    currency_code = forms.ChoiceField(
        label=_('The Currency You Want to Trade for BTC'),
        choices=BFH_CURRENCY_DROPDOWN,
        required=True,
        widget=forms.Select(),
    )
    btc_address = forms.CharField(
            label=_('Bitcoin Deposit Address'),
            required=True,
            min_length=27,
            max_length=34,
            help_text=_('The wallet address where you want your bitcoin sent'),
            widget=forms.TextInput(),
    )
    btc_markup = forms.DecimalField(
            label=_('Percent Markup'),
            required=True,
            validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
            help_text=_('The percent you want to charge above the market rate'),
            widget=forms.TextInput(),
    )

    def __init__(self, AuthUser, *args, **kwargs):
        self.AuthUser = AuthUser
        super(MerchantRegistrationForm, self).__init__(*args, **kwargs)
        if kwargs and 'initial' in kwargs and 'currency_code' in kwargs['initial']:
            self.fields['currency_code'].widget.attrs['data-currency'] = kwargs['initial']['currency_code']

    def clean_btc_address(self):
        address = self.cleaned_data.get('btc_address')
        if not is_valid_btc_address(address):
            msg = _("Sorry, that's not a valid bitcoin address")
            raise forms.ValidationError(msg)
        return address

    def clean_email(self):
        email = self.cleaned_data['email']
        existing_user = get_object_or_None(self.AuthUser, username=email)
        if existing_user:
            # TODO: move this to clean_email
            login_url = '%s?e=%s' % (reverse('login_request'), existing_user.email)
            msg = _('That email is already taken, do you want to <a href="%s">login</a>?' % login_url)
            raise forms.ValidationError(mark_safe(msg))

        if len(email) > 30:
            msg = _('Sorry, your email address must be less than 31 characters')
            raise forms.ValidationError(msg)
        return email


class AccountRegistrationForm(forms.Form):
    email = forms.EmailField(
        label=_('Email'),
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )

    password = forms.CharField(
        required=True,
        label=_('Password'),
        widget=forms.PasswordInput(),
        min_length=7,
    )


class OwnerInfoForm(forms.Form):
    full_name = forms.CharField(
        label=_('Your Name'),
        required=True,
        min_length=2,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': 'John Smith'}),
    )

    email = forms.EmailField(
        label=_('Email'),
        required=True,
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


class MerchantInfoForm(forms.Form):

    business_name = forms.CharField(
        label=_('Business Name'),
        required=True,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(attrs={'placeholder': _("Mel's Diner")}),
    )

    address_1 = forms.CharField(
        label=_('Address Line 1'),
        min_length=5,
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Street address, P.O. box, company name, c/o ')}),
    )

    address_2 = forms.CharField(
        label=_('Address Line 2'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Apartment, suite, unit, building, floor, etc.')}),
    )

    city = forms.CharField(
        label='City',
        required=False,
        max_length=30,
        widget=forms.TextInput(),
    )
    state = forms.CharField(
        label=_('State/Province/Region'),
        required=False,
        min_length=2,
        max_length=30,
        widget=forms.TextInput(),
    )

    zip_code = forms.CharField(
        label=_('Zip Code'),
        min_length=3,
        max_length=30,
        required=False,
        widget=forms.TextInput(),
    )
    country = forms.ChoiceField(
        required=True,
        choices=COUNTRY_DROPDOWN,
        widget=forms.Select(attrs={'data-country': 'USA'}),
    )

    phone_num = forms.CharField(
        label=_('Phone Number'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'bfh-phone', 'data-country': 'id_country'}),
    )

    clean_phone_num = clean_phone_num


class BitcoinInfoForm(forms.Form):

    currency_code = forms.ChoiceField(
        label=_('The Currency You Want to Trade for BTC'),
        required=True,
        choices=BFH_CURRENCY_DROPDOWN,
        widget=forms.Select(),
    )

    btc_address = forms.CharField(
            label=_('Bitcoin Deposit Address'),
            required=True,
            min_length=27,
            max_length=34,
            help_text=_('The wallet address where you want your bitcoin sent'),
            widget=forms.TextInput(),
    )

    btc_markup = forms.DecimalField(
            label=_('Percent Markup'),
            required=True,
            validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
            help_text=_('The percent you want to charge above the market rate.'),
            widget=forms.TextInput(),
    )

    def __init__(self, *args, **kwargs):
        super(BitcoinInfoForm, self).__init__(*args, **kwargs)
        if kwargs and 'initial' in kwargs and 'currency_code' in kwargs['initial']:
            self.fields['currency_code'].widget.attrs['data-currency'] = kwargs['initial']['currency_code']

    def clean_btc_address(self):
        address = self.cleaned_data.get('btc_address')
        if not is_valid_btc_address(address):
            msg = _("Sorry, that's not a valid bitcoin address")
            raise forms.ValidationError(msg)
        return address
