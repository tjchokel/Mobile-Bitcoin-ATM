from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import ugettext_lazy as _

from bitcoins.BCAddressField import is_valid_btc_address
from django.utils.safestring import mark_safe
from annoying.functions import get_object_or_None

from countries import COUNTRY_DROPDOWN, BFH_CURRENCY_DROPDOWN

from utils import clean_phone_num

from unidecode import unidecode


def clean_full_name(self):
    """ Helper function for transliterating full_name field """
    return unidecode(self.cleaned_data['full_name'])


def clean_business_name(self):
    """ Helper function for transliterating business_name field """
    return unidecode(self.cleaned_data['business_name'])


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

    def clean_email(self):
        email = self.cleaned_data['email']
        return email.lower().strip()


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

    def __init__(self, AuthUser, *args, **kwargs):
        self.AuthUser = AuthUser
        super(MerchantRegistrationForm, self).__init__(*args, **kwargs)
        if kwargs and 'initial' in kwargs and 'currency_code' in kwargs['initial']:
            self.fields['currency_code'].widget.attrs['data-currency'] = kwargs['initial']['currency_code']

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        existing_user = get_object_or_None(self.AuthUser, username=email)
        if existing_user:
            login_uri = existing_user.get_login_uri()
            msg = _('That email is already taken, do you want to <a href="%(login_uri)s">login</a>?') % {'login_uri': login_uri}
            raise forms.ValidationError(mark_safe(msg))

        if len(email) > 100:
            msg = _('Sorry, your email address must be less than 100 characters')
            raise forms.ValidationError(msg)
        return email

    clean_full_name = clean_full_name
    clean_business_name = clean_business_name


class BitcoinRegistrationForm(forms.Form):

    btc_markup = forms.DecimalField(
        label=_('Percent Markup'),
        required=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_('The percent you want to charge above the market rate'),
        widget=forms.TextInput(),
    )

    wallet_type_choice = forms.ChoiceField(
        label=_('Wallet Choice'),
        required=True,
        widget=forms.RadioSelect(attrs={'id': 'wallet_type_choice'}),
        choices=(
            ('new', _('Create New blockchain.info Wallet')),
            ('old', _('Link Existing Hosted Wallet')),
            ),
    )

    new_blockchain_password = forms.CharField(
        label=_('New Blockchain Wallet Password'),
        required=False,
        min_length=10,
        max_length=256,
        widget=forms.PasswordInput(render_value=False, attrs={'id': 'pass1'}),
        help_text=_('Do not forget this password! Blockchain.info does not support password recovery.'),
    )

    new_blockchain_password_confirm = forms.CharField(
        label=_('Confirm Password'),
        required=False,
        min_length=10,
        max_length=256,
        widget=forms.PasswordInput(render_value=False, attrs={'id': 'pass2'}),
    )

    exchange_choice = forms.ChoiceField(
        label=_('Existing Bitcoin Wallet Provider'),
        required=True,
        widget=forms.RadioSelect(attrs={'id': 'exchange_choice'}),
        choices=(
            ('coinbase', 'coinbase.com'),
            ('blockchain', 'blockchain.info'),
            ('bitstamp', 'bitstamp.net'),
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

    def clean_new_blockchain_password(self):
        wallet_type_choice = self.cleaned_data.get('wallet_type_choice')
        new_blockchain_password = self.cleaned_data.get('new_blockchain_password').strip()
        if wallet_type_choice == 'new' and not new_blockchain_password:
            msg = _('Please enter a Blockchain.info password')
            raise forms.ValidationError(msg)
        return new_blockchain_password

    def clean_cb_api_key(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        wallet_type_choice = self.cleaned_data.get('wallet_type_choice')
        cb_api_key = self.cleaned_data.get('cb_api_key').strip()
        if exchange_choice == 'coinbase' and not cb_api_key and wallet_type_choice == 'old':
            msg = _('Please enter your Coinbase API key')
            raise forms.ValidationError(msg)
        return cb_api_key

    def clean_cb_secret_key(self):
        exchange_choice = self.cleaned_data.get('exchange_choice')
        wallet_type_choice = self.cleaned_data.get('wallet_type_choice')
        cb_secret_key = self.cleaned_data.get('cb_secret_key').strip()
        if exchange_choice == 'coinbase' and not cb_secret_key and wallet_type_choice == 'old':
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

    def clean(self):
        wallet_type_choice = self.cleaned_data.get('wallet_type_choice')
        if wallet_type_choice == 'new':
            pw = self.cleaned_data.get('new_blockchain_password')
            pwc = self.cleaned_data.get('new_blockchain_password_confirm')
            if pw != pwc:
                err_msg = _('Those passwords did not match. Please try again.')
                raise forms.ValidationError(err_msg)

        return self.cleaned_data


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
        # TODO: the way errors are handled in the views will not display this
        # correctly to users
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
    clean_full_name = clean_full_name


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
        label=_('City'),
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

    website = forms.CharField(
            label=_('Website URL'),
            required=False,
            )

    clean_phone_num = clean_phone_num
    clean_business_name = clean_business_name


class BusinessHoursForm(forms.Form):
    HOURS = (
                ('-1', 'Not Open Today'),
                ('1', '1:00 am'),
                ('2', '2:00 am'),
                ('3', '3:00 am'),
                ('4', '4:00 am'),
                ('5', '5:00 am'),
                ('6', '6:00 am'),
                ('7', '7:00 am'),
                ('8', '8:00 am'),
                ('9', '9:00 am'),
                ('10', '10:00 am'),
                ('11', '11:00 am'),
                ('12', '12:00 pm - noon'),
                ('13', '1:00 pm'),
                ('14', '2:00 pm'),
                ('15', '3:00 pm'),
                ('16', '4:00 pm'),
                ('17', '5:00 pm'),
                ('18', '6:00 pm'),
                ('19', '7:00 pm'),
                ('20', '8:00 pm'),
                ('21', '9:00 pm'),
                ('22', '10:00 pm'),
                ('23', '11:00 pm'),
                ('24', '12:00 am - midnight'),
                )

    monday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%; display:inline;'}))
    monday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%; display:inline;'}))
    tuesday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    tuesday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    wednesday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    wednesday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    thursday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    thursday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    friday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    friday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    saturday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    saturday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    sunday_open = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))
    sunday_close = forms.ChoiceField(required=True, choices=HOURS, widget=forms.Select(attrs={'style': 'width:20%;'}))


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

    cashin_markup_in_bps = forms.DecimalField(
            label=_('Percent Markup When Selling Bitcoin'),
            required=True,
            validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
            help_text=_('The percentage you charge above the market price when selling bitcoin'),
            widget=forms.TextInput(),
    )

    cashout_markup_in_bps = forms.DecimalField(
            label=_('Percent Markup When Buying Bitcoin'),
            required=True,
            validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
            help_text=_('The percentage you pay below the market price when buying bitcoin.'),
            widget=forms.TextInput(),
    )

    max_mbtc_shopper_purchase = forms.IntegerField(
            label=_('Max Shopper Purchase'),
            required=True,
            help_text=_('The maximum amount of mBTC a shopper can purchase.'),
            widget=forms.TextInput(),
    )

    max_mbtc_shopper_sale = forms.IntegerField(
            label=_('Max Shopper Sale'),
            required=True,
            help_text=_('The maximum amount of mBTC a shopper can sell.'),
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


class PasswordConfirmForm(forms.Form):
    redir_path = forms.CharField(
            required=False,
            widget=forms.HiddenInput(),
            )

    password = forms.CharField(
        label=_('CoinSafe Password'),
        required=True,
        widget=forms.PasswordInput(render_value=False)
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(PasswordConfirmForm, self).__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not self.user.check_password(password):
            raise forms.ValidationError('Invalid password')
