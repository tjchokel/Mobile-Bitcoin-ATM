from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from merchants.models import Merchant
from users.models import AuthUser, LoggedLogin

from coinbase_wallets.models import CBSCredential
from blockchain_wallets.models import BCICredential
from bitstamp_wallets.models import BTSCredential

from merchants.forms import (LoginForm, MerchantRegistrationForm, BitcoinRegistrationForm,
        BitcoinInfoForm, BusinessHoursForm, OwnerInfoForm, MerchantInfoForm)

import datetime


@sensitive_variables('password', )
@sensitive_post_parameters('password', )
@render_to('login.html')
def login_request(request):
    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Log in user
            email = form.cleaned_data['email'].lower().strip()
            password = form.cleaned_data['password']

            user_found = get_object_or_None(AuthUser, username=email)
            if user_found:
                user = authenticate(username=email, password=password)
                if user:
                    login(request, user)

                    # Log the login
                    LoggedLogin.record_login(request)

                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    msg = _("Sorry, that's not the right password for <b>%s</b>." % escape(email))
                    messages.warning(request, msg, extra_tags='safe')
            else:
                msg = _("No account found for <b>%s</b>." % escape(email))
                messages.warning(request, msg, extra_tags='safe')

    elif request.method == 'GET':
        email = request.GET.get('e')
        if email:
            form = LoginForm(initial={'email': email})

    return {'form': form}


def logout_request(request):
    " Log a user out using Django's logout function and redirect them "
    logout(request)
    msg = _("You Are Now Logged Out")
    messages.success(request, msg)
    return HttpResponseRedirect(reverse_lazy('login_request'))


def register_router(request):
    user = request.user
    if not user.is_authenticated():  # if user is not authenticated
        return HttpResponsePermanentRedirect(reverse_lazy('register_merchant'))
    merchant = user.get_merchant()
    if merchant and merchant.has_finished_registration():
        return HttpResponsePermanentRedirect(reverse_lazy('customer_dashboard'))
    else:
        return HttpResponsePermanentRedirect(reverse_lazy('register_bitcoin'))


@render_to('merchants/register.html')
def register_merchant(request):
    user = request.user
    if user.is_authenticated():
        merchant = user.get_merchant()
        if merchant and merchant.has_finished_registration():
            return HttpResponsePermanentRedirect(reverse_lazy('customer_dashboard'))
        else:
            return HttpResponsePermanentRedirect(reverse_lazy('register_bitcoin'))
    initial = {
        'country': 'USA',
        'currency_code': 'USD',
    }
    form = MerchantRegistrationForm(AuthUser=AuthUser, initial=initial)
    form_valid = True  # used to decide whether we run the JS or not
    if request.method == 'POST':
        form = MerchantRegistrationForm(AuthUser=AuthUser, data=request.POST)
        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']
            business_name = form.cleaned_data['business_name']
            country = form.cleaned_data['country']
            currency_code = form.cleaned_data['currency_code']

            # create user
            user = AuthUser.objects.create_user(
                    email,
                    email=email,
                    password=password,
                    full_name=full_name,
            )

            # Create merchant
            merchant = Merchant.objects.create(
                    user=user,
                    business_name=business_name,
                    country=country,
                    currency_code=currency_code,
            )

            # login user
            user_to_login = authenticate(username=email, password=password)
            login(request, user_to_login)

            # Log the login
            LoggedLogin.record_login(request)

            return HttpResponseRedirect(reverse_lazy('register_bitcoin'))

        else:
            form_valid = False

    elif request.method == 'GET':
        email = request.GET.get('e')
        if email:
            initial['email'] = email
            form = MerchantRegistrationForm(AuthUser=AuthUser, initial=initial)

    return {'form': form, 'user': user, 'form_valid': form_valid}


@sensitive_variables('cb_api_key', 'cb_secret_key', 'bs_api_key', 'bs_secret_key')
@sensitive_post_parameters('cb_api_key', 'cb_secret_key', 'bs_api_key', 'bs_secret_key')
@render_to('merchants/register_bitcoin.html')
def register_bitcoin(request):
    user = request.user
    if not user.is_authenticated():
        return HttpResponseRedirect(reverse_lazy('register_merchant'))
    merchant = user.get_merchant()
    if not merchant:
        return HttpResponseRedirect(reverse_lazy('register_merchant'))
    if merchant.has_valid_api_credential():
        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))

    initial = {
            'btc_markup': 2.0,
            'exchange_choice': 'coinbase',
    }
    form = BitcoinRegistrationForm(initial=initial)
    if request.method == 'POST':
        form = BitcoinRegistrationForm(data=request.POST)
        if form.is_valid():
            exchange_choice = form.cleaned_data['exchange_choice']
            btc_address = form.cleaned_data['btc_address']
            basis_points_markup = form.cleaned_data['btc_markup']
            merchant.basis_points_markup = basis_points_markup * 100
            merchant.save()
            if exchange_choice == 'selfmanaged':
                merchant.set_destination_address(btc_address, credential_used=None)
                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
            else:
                if exchange_choice == 'coinbase':
                    credential = CBSCredential.objects.create(
                            merchant=merchant,
                            api_key=form.cleaned_data['cb_api_key'],
                            api_secret=form.cleaned_data['cb_secret_key'],
                            )
                elif exchange_choice == 'bitstamp':
                    credential = BTSCredential.objects.create(
                            merchant=merchant,
                            customer_id=form.cleaned_data['bs_customer_id'],
                            api_key=form.cleaned_data['bs_api_key'],
                            api_secret=form.cleaned_data['bs_secret_key'],
                            )
                elif exchange_choice == 'blockchain':
                    credential = BCICredential.objects.create(
                            merchant=merchant,
                            username=form.cleaned_data['bci_username'],
                            main_password=form.cleaned_data['bci_main_password'],
                            second_password=form.cleaned_data['bci_second_password'],
                            )
                try:
                    # Get new address if API partner permits, otherwise get an existing one
                    credential.get_best_receiving_address(set_as_merchant_address=True)

                    msg = _('Your account has been created! Customers can use this page while at your store to trade bitcoin with you.')
                    messages.success(request, msg)
                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                except:
                    credential.mark_disabled()
                    messages.warning(request, _('Your API credentials are not valid. Please try again.'))

    return {'form': form, 'user': user}


@login_required
@render_to('merchants/settings.html')
def merchant_settings(request):
    user = request.user
    merchant = user.get_merchant()
    if not merchant or not merchant.has_finished_registration():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    dest_address = merchant.get_destination_address()
    initial = {}

    initial['currency_code'] = merchant.currency_code
    initial['btc_address'] = dest_address.b58_address
    initial['btc_markup'] = merchant.basis_points_markup / 100.0
    bitcoin_form = BitcoinInfoForm(initial=initial)
    return {
        'user': user,
        'merchant': merchant,
        'on_admin_page': True,
        'bitcoin_form': bitcoin_form,
        'dest_address': dest_address
    }


@login_required
@render_to('merchants/profile.html')
def merchant_profile(request):
    user = request.user
    merchant = user.get_merchant()
    if not merchant or not merchant.has_finished_registration():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    transactions = merchant.get_all_forwarding_transactions()
    initial = {}
    initial['full_name'] = user.full_name
    initial['email'] = user.email
    initial['phone_num'] = user.phone_num
    initial['phone_country'] = user.phone_num_country or merchant.country

    initial['business_name'] = merchant.business_name
    initial['address_1'] = merchant.address_1
    initial['address_2'] = merchant.address_2
    initial['city'] = merchant.city
    initial['state'] = merchant.state
    initial['zip_code'] = merchant.zip_code
    initial['country'] = merchant.country
    initial['phone_num'] = merchant.phone_num
    website_obj = merchant.get_website()
    if website_obj:
        initial['website'] = website_obj.url

    # biz hours, so WET :(
    hours_formatted = merchant.get_hours_formatted()
    if hours_formatted.get(1):
        initial['monday_open'] = hours_formatted.get(1)['from_time'].hour
        initial['monday_close'] = hours_formatted.get(1)['to_time'].hour
    if hours_formatted.get(2):
        initial['tuesday_open'] = hours_formatted.get(2)['from_time'].hour
        initial['tuesday_close'] = hours_formatted.get(2)['to_time'].hour
    if hours_formatted.get(3):
        initial['wednesday_open'] = hours_formatted.get(3)['from_time'].hour
        initial['wednesday_close'] = hours_formatted.get(3)['to_time'].hour
    if hours_formatted.get(4):
        initial['thursday_open'] = hours_formatted.get(4)['from_time'].hour
        initial['thursday_close'] = hours_formatted.get(4)['to_time'].hour
    if hours_formatted.get(5):
        initial['friday_open'] = hours_formatted.get(5)['from_time'].hour
        initial['friday_close'] = hours_formatted.get(5)['to_time'].hour
    if hours_formatted.get(6):
        initial['saturday_open'] = hours_formatted.get(6)['from_time'].hour
        initial['saturday_close'] = hours_formatted.get(6)['to_time'].hour
    if hours_formatted.get(7):
        initial['sunday_open'] = hours_formatted.get(7)['from_time'].hour
        initial['sunday_close'] = hours_formatted.get(7)['to_time'].hour

    return {
        'user': user,
        'merchant': merchant,
        'transactions': transactions,
        'on_admin_page': True,
        'personal_form': OwnerInfoForm(initial=initial),
        'merchant_form': MerchantInfoForm(initial=initial),
        'hours_form': BusinessHoursForm(initial=initial),
        'biz_hours': hours_formatted,
    }


@login_required
@render_to('merchants/transactions.html')
def merchant_transactions(request):
    user = request.user
    merchant = user.get_merchant()
    if not merchant or not merchant.has_finished_registration():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    transactions = merchant.get_combined_transactions()
    return {
        'user': user,
        'merchant': merchant,
        'transactions': transactions,
        'on_admin_page': True
    }


@login_required
def edit_personal_info(request):
    user = request.user
    if request.method == 'POST':
        form = OwnerInfoForm(data=request.POST)
        if form.is_valid():

            user.full_name = form.cleaned_data['full_name']
            user.phone_num = form.cleaned_data['phone_num']
            user.phone_num_country = form.cleaned_data['phone_country']
            user.email = form.cleaned_data['email']
            user.username = form.cleaned_data['email']
            user.save()

            msg = _('Your profile has been updated')
            messages.success(request, msg)
            return HttpResponseRedirect(reverse_lazy('merchant_profile'))

    msg = _('Your profile was not updated')
    messages.warning(request, msg)
    return HttpResponseRedirect(reverse_lazy('merchant_profile'))


@login_required
def edit_hours_info(request):
    user = request.user
    if request.method == 'POST':
        form = BusinessHoursForm(data=request.POST)
        if form.is_valid():

            merchant = user.get_merchant()

            monday_open = int(form.cleaned_data['monday_open'])
            monday_close = int(form.cleaned_data['monday_close'])
            tuesday_open = int(form.cleaned_data['tuesday_open'])
            tuesday_close = int(form.cleaned_data['tuesday_close'])
            wednesday_open = int(form.cleaned_data['wednesday_open'])
            wednesday_close = int(form.cleaned_data['wednesday_close'])
            thursday_open = int(form.cleaned_data['thursday_open'])
            thursday_close = int(form.cleaned_data['thursday_close'])
            friday_open = int(form.cleaned_data['friday_open'])
            friday_close = int(form.cleaned_data['friday_close'])
            saturday_open = int(form.cleaned_data['saturday_open'])
            saturday_close = int(form.cleaned_data['saturday_close'])
            sunday_open = int(form.cleaned_data['sunday_open'])
            sunday_close = int(form.cleaned_data['sunday_close'])

            hours = []

            if monday_open > 0 and monday_close > 0:
                hours.append((1, datetime.time(monday_open), datetime.time(monday_close)))
            if tuesday_open > 0 and tuesday_close > 0:
                hours.append((2, datetime.time(tuesday_open), datetime.time(tuesday_close)))
            if wednesday_open > 0 and wednesday_close > 0:
                hours.append((3, datetime.time(wednesday_open), datetime.time(wednesday_close)))
            if thursday_open > 0 and thursday_close > 0:
                hours.append((4, datetime.time(thursday_open), datetime.time(thursday_close)))
            if friday_open > 0 and friday_close > 0:
                hours.append((5, datetime.time(friday_open), datetime.time(friday_close)))
            if saturday_open > 0 and saturday_close > 0:
                hours.append((6, datetime.time(saturday_open), datetime.time(saturday_close)))
            if sunday_open > 0 and sunday_close > 0:
                hours.append((7, datetime.time(sunday_open), datetime.time(sunday_close)))

            merchant.set_hours(hours)

            msg = _('Your business hours have been updated')
            messages.success(request, msg)
            return HttpResponseRedirect(reverse_lazy('merchant_profile'))

    msg = _('Your business hours have not been updated')
    messages.warning(request, msg)
    return HttpResponseRedirect(reverse_lazy('merchant_profile'))


@login_required
def edit_merchant_info(request):
    user = request.user
    merchant = user.get_merchant()
    if request.method == 'POST' and merchant:
        form = MerchantInfoForm(data=request.POST)
        if form.is_valid():

            merchant.business_name = form.cleaned_data['business_name']
            merchant.address_1 = form.cleaned_data['address_1']
            merchant.address_2 = form.cleaned_data['address_2']
            merchant.city = form.cleaned_data['city']
            merchant.state = form.cleaned_data['state']
            merchant.country = form.cleaned_data['country']
            merchant.zip_code = form.cleaned_data['zip_code']
            merchant.phone_num = form.cleaned_data['phone_num']
            merchant.save()

            website = form.cleaned_data['website']
            merchant.set_website(website)

            messages.success(request, _('Your business info has been updated'))
            return HttpResponseRedirect(reverse_lazy('merchant_profile'))

    messages.warning(request, _('Your business info was not updated'))
    return HttpResponseRedirect(reverse_lazy('merchant_profile'))


@login_required
def edit_bitcoin_info(request):
    user = request.user
    merchant = user.get_merchant()
    if request.method == 'POST' and merchant:
        form = BitcoinInfoForm(data=request.POST)
        if form.is_valid():

            merchant.currency_code = form.cleaned_data['currency_code']
            merchant.set_destination_address(
                    dest_address=form.cleaned_data['btc_address'],
                    credential_used=None)
            merchant.basis_points_markup = form.cleaned_data['btc_markup'] * 100
            merchant.save()

            messages.success(request, _('Your bitcoin info has been updated'))
            return HttpResponseRedirect(reverse_lazy('merchant_settings'))

    messages.warning(request, _('Your bitcoin info was not updated'))
    return HttpResponseRedirect(reverse_lazy('merchant_settings'))
