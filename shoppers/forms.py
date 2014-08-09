from django import forms
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator
from countries import COUNTRY_DROPDOWN
from decimal import Decimal

from bitcoins.BCAddressField import is_valid_btc_address
from bitcoins.models import BTCTransaction

from utils import clean_phone_num, STANDARD_TX_FEE_IN_SATOSHIS, mbtc_to_satoshis

from unidecode import unidecode


class ShopperInformationForm(forms.Form):
    name = forms.CharField(
        required=True,
        label=_('Customer Name'),
        widget=forms.TextInput(attrs={'placeholder': 'John Smith'}),
        min_length=2,
    )

    email = forms.EmailField(
        label=_('Customer Email'),
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'me@example.com'}),
    )

    phone_country = forms.ChoiceField(
        label=_('Country'),
        required=False,
        choices=COUNTRY_DROPDOWN,
        widget=forms.Select(attrs={'data-country': 'USA'}),
    )

    phone_num = forms.CharField(
        label=_('Customer Mobile Phone'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'bfh-phone', 'data-country': 'id_phone_country'}),
    )

    clean_phone_num = clean_phone_num

    def clean_name(self):
        return unidecode(self.cleaned_data['name'])


def clean_amount(self):
    """
    Function used in both BuyBitcoinForm and NoEmailBuyBitcoinForm

    DRY-ing it out here
    """
    amount = self.cleaned_data.get('amount').replace(',', '')
    amount = Decimal(amount)
    merchant = self.merchant

    # Check if amount exceeds merhcant's buy limit
    max_mbtc_shopper_purchase = merchant.max_mbtc_shopper_purchase
    btc_price = Decimal(BTCTransaction.get_btc_market_price(merchant.currency_code))
    amount_in_mbtc = (amount / btc_price) * 1000
    if amount_in_mbtc < 1:
        msg = _("Sorry, you must buy at least 1 mBTC")
        raise forms.ValidationError(msg)
    if max_mbtc_shopper_purchase < amount_in_mbtc:
        msg = _("Sorry, the amount you entered exceeds the purchase limit (%s mBTC)" % max_mbtc_shopper_purchase)
        raise forms.ValidationError(msg)

    # Check if amount exceeds available balance
    credential = merchant.get_valid_api_credential()
    if credential:
        balance = credential.get_balance()
        if balance is False:
            # This will incorrecty display on the amount input and not the form as a whole
            # That's worth it here for simplicity and not having to make 2 API calls
            msg = _("Sorry, the business API credentials for %s are invalid." % credential.get_credential_to_display())
            raise forms.ValidationError(msg)
        elif balance < (mbtc_to_satoshis(float(amount_in_mbtc))*1.01 + 2*STANDARD_TX_FEE_IN_SATOSHIS):
            # The 1% increase is hackey buffer for the fact that the price isn't locked in.
            # The 2x standard fee is a hackey buffer for the fees
            msg = _("Sorry, the amount you entered exceeds the available balance")
            raise forms.ValidationError(msg)
    return amount


class BuyBitcoinForm(forms.Form):
    amount = forms.CharField(
        label=_('Amount of Cash to Pay'),
        required=True,
        help_text=_('This is what you will give to the cashier'),
        widget=forms.TextInput(attrs={'class': 'needs-input-group', 'placeholder': '0', 'style': 'width:50%;'}),
    )

    email = forms.EmailField(
        label=_('Customer Email'),
        required=True,
        widget=forms.TextInput(attrs={'id': 'email-field', 'placeholder': 'me@example.com', 'style': 'width:55%;'}),
    )

    email_or_btc_address = forms.ChoiceField(
        label=_('Send Bitcoin to Email or BTC Address'),
        required=True,
        widget=forms.RadioSelect(attrs={'id': 'address'}),
        choices=(('1', 'Email Address',), ('2', 'Bitcoin Address',)),
    )

    btc_address = forms.CharField(
        label=_('Bitcoin Deposit Address'),
        required=False,
        help_text=_('The wallet address where you want your bitcoin sent'),
        widget=forms.TextInput(attrs={'style': 'width:55%; display:inline;'}),
    )

    def __init__(self, merchant, *args, **kwargs):
        self.merchant = merchant
        super(BuyBitcoinForm, self).__init__(*args, **kwargs)

    def clean_btc_address(self):
        address = self.cleaned_data.get('btc_address')
        email_or_btc_address = self.cleaned_data.get('email_or_btc_address')
        # sending to a bitcoin address
        if email_or_btc_address == '2':
            if not is_valid_btc_address(address):
                msg = _("Please enter a valid bitcoin address")
                raise forms.ValidationError(msg)
        return address

    clean_amount = clean_amount


class NoEmailBuyBitcoinForm(forms.Form):
    amount = forms.CharField(
        label=_('Amount of Cash to Pay'),
        required=True,
        help_text=_('This is what you will give to the cashier'),
        widget=forms.TextInput(attrs={'class': 'needs-input-group', 'placeholder': '0', 'style': 'width:50%;'}),
    )

    email = forms.EmailField(
        label=_('Customer Email'),
        required=True,
        widget=forms.TextInput(attrs={'id': 'email-field', 'placeholder': 'me@example.com', 'style': 'width:55%;'}),
    )

    btc_address = forms.CharField(
        label=_('Customer Bitcoin Address'),
        required=True,
        min_length=27,
        max_length=34,
        help_text=_('The wallet address where you want to receive your bitcoin'),
        widget=forms.TextInput(attrs={'style': 'width:55%; display:inline;'}),
    )

    def __init__(self, merchant, *args, **kwargs):
        self.merchant = merchant
        super(NoEmailBuyBitcoinForm, self).__init__(*args, **kwargs)

    def clean_btc_address(self):
        address = self.cleaned_data.get('btc_address')
        if not is_valid_btc_address(address):
            msg = _("Sorry, that's not a valid bitcoin address")
            raise forms.ValidationError(msg)
        return address

    clean_amount = clean_amount


class ConfirmPasswordForm(forms.Form):
    password = forms.CharField(
        required=True,
        label=_('Verify Merchant Password'),
        widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError(_('Invalid password'))

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(ConfirmPasswordForm, self).__init__(*args, **kwargs)
