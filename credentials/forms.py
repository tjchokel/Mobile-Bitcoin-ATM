from django import forms
from django.utils.translation import ugettext_lazy as _

from bitcoins.BCAddressField import is_valid_btc_address


class BitcoinCredentialsForm(forms.Form):

    exchange_choice = forms.ChoiceField(
        label=_('Your Bitcoin Wallet Provider'),
        required=True,
        widget=forms.RadioSelect(attrs={'id': 'exchange_choice'}),
        choices=(
            ('coinbase', 'Coinbase'),
            ('blockchain', 'blockchain.info'),
            ('bitstamp', 'Bitstamp'),
            ('selfmanaged', _('Self Managed')),
            ),
    )

    cb_api_key = forms.CharField(
        label=_('Coinbase API Key'),
        required=False,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(),
    )

    cb_secret_key = forms.CharField(
        label=_('Coinbase Secret Key'),
        min_length=5,
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
    )

    bs_customer_id = forms.CharField(
        label=_('Bitstamp Customer ID'),
        required=False,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(),
    )

    bs_api_key = forms.CharField(
        label=_('Bitstamp API Key'),
        required=False,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(),
    )

    bs_secret_key = forms.CharField(
        label=_('Bitstamp Secret Key'),
        min_length=5,
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
    )

    bci_username = forms.CharField(
        label=_('Blockchain Username (Wallet Identifier)'),
        required=False,
        min_length=5,
        max_length=256,
        widget=forms.TextInput(),
    )

    bci_main_password = forms.CharField(
        label=_('Blockchain Main Password'),
        required=False,
        min_length=5,
        max_length=256,
        widget=forms.PasswordInput(render_value=False),
    )

    bci_second_password = forms.CharField(
        label=_('Blockchain Second Password'),
        required=False,
        min_length=5,
        max_length=256,
        widget=forms.PasswordInput(render_value=False),
    )

    btc_address = forms.CharField(
            label=_('Bitcoin Deposit Address'),
            required=True,
            min_length=27,
            max_length=34,
            help_text=_('The wallet address where you want your bitcoin sent'),
            widget=forms.TextInput(),
    )

    def clean_cb_api_key(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        cb_api_key = self.cleaned_data.get('cb_api_key').strip()
        if exchange_choice == 'coinbase' and not cb_api_key:
            msg = _('Please enter your Coinbase API key')
            raise forms.ValidationError(msg)
        return cb_api_key

    def clean_cb_secret_key(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        cb_secret_key = self.cleaned_data.get('cb_secret_key').strip()
        if exchange_choice == 'coinbase' and not cb_secret_key:
            msg = _('Please enter your Coinbase secret key')
            raise forms.ValidationError(msg)
        return cb_secret_key

    def clean_bs_customer_id(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        bs_customer_id = self.cleaned_data.get('bs_customer_id').strip()
        if exchange_choice == 'bitstamp' and not bs_customer_id:
            msg = _('Please enter your Bitstamp username')
            raise forms.ValidationError(msg)
        return bs_customer_id

    def clean_bs_api_key(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        bs_api_key = self.cleaned_data.get('bs_api_key').strip()
        if exchange_choice == 'bitstamp' and not bs_api_key:
            msg = _('Please enter your Bitstamp API key')
            raise forms.ValidationError(msg)
        return bs_api_key

    def clean_bs_secret_key(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        bs_secret_key = self.cleaned_data.get('bs_secret_key').strip()
        if exchange_choice == 'bitstamp' and not bs_secret_key:
            msg = _('Please enter your Bitstamp Secret Key')
            raise forms.ValidationError(msg)
        return bs_secret_key

    def clean_bci_username(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        bci_username = self.cleaned_data.get('bci_username').strip()
        if exchange_choice == 'blockchain' and not bci_username:
            msg = _('Please enter your Blockchain username')
            raise forms.ValidationError(msg)
        if bci_username.startswith('https://blockchain.info/wallet/'):
            bci_username = bci_username.lstrip('https://blockchain.info/wallet/')
        return bci_username

    def clean_bci_main_password(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        bci_main_password = self.cleaned_data.get('bci_main_password').strip()
        if exchange_choice == 'blockchain' and not bci_main_password:
            msg = _('Please enter your Blockchain API key')
            raise forms.ValidationError(msg)
        return bci_main_password

    def clean_btc_address(self):
        address = self.cleaned_data.get('btc_address').strip()
        exchange_choice = self.cleaned_data.get('exchange_choice')
        if address and not is_valid_btc_address(address):
            msg = _("Sorry, that's not a valid bitcoin address")
            raise forms.ValidationError(msg)
        if exchange_choice == 'selfmanaged' and not is_valid_btc_address(address):
            msg = _("Please enter a valid bitcoin address")
            raise forms.ValidationError(msg)
        return address


SENSITIVE_CRED_PARAMS = ('cb_api_key', 'cb_secret_key', 'bci_username', 'bci_main_password', 'bci_second_password', 'bs_customer_id', 'bs_api_key', 'bs_secret_key')
