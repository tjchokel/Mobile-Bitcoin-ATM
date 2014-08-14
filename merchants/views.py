from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters
from django.utils.timezone import now
import datetime

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from merchants.models import Merchant
from users.models import AuthUser, LoggedLogin

from coinbase_wallets.models import CBSCredential
from blockchain_wallets.models import BCICredential
from bitstamp_wallets.models import BTSCredential

from merchants.forms import (LoginForm, MerchantRegistrationForm, BitcoinRegistrationForm,
        BitcoinInfoForm, BusinessHoursForm, OwnerInfoForm, MerchantInfoForm, PasswordConfirmForm)


@sensitive_variables('password', )
@sensitive_post_parameters('password', )
@render_to('login.html')
def login_request(request):
    form = LoginForm()

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Log in user
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user_found = get_object_or_None(AuthUser, username=email)
            if user_found:
                user = authenticate(username=email, password=password)
                if user:
                    login(request, user)

                    request.session['last_password_validation'] = now().ctime()

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
                    username=email.lower(),
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

            # Send welcome email (it's really for later)
            merchant.send_welcome_email()

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
            'wallet_type_choice': 'new',
    }
    form = BitcoinRegistrationForm(initial=initial)
    if request.method == 'POST':
        form = BitcoinRegistrationForm(data=request.POST)
        if form.is_valid():
            wallet_type_choice = form.cleaned_data['wallet_type_choice']
            exchange_choice = form.cleaned_data['exchange_choice']
            basis_points_markup = form.cleaned_data['btc_markup']
            merchant.cashin_markup_in_bps = basis_points_markup * 100
            merchant.cashout_markup_in_bps = basis_points_markup * 100
            merchant.save()

            SUCCESS_MSG = _('Your account has been configured! Customers can use this page while at your store to trade bitcoin with you.')
            DASHBOARD_URI = reverse_lazy('customer_dashboard')

            if wallet_type_choice == 'new':
                new_btc_address = BCICredential.create_wallet_credential(
                        user_password=form.cleaned_data['new_blockchain_password'],
                        merchant=merchant,
                        user_email=merchant.user.email)
                merchant.set_destination_address(new_btc_address)
                SUCCESS_MSG = _('Your blockchain.info wallet has been created! Customers can use this page while at your store to trade bitcoin with you.')
                messages.success(request, SUCCESS_MSG)
                return HttpResponseRedirect(DASHBOARD_URI)

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
                    messages.success(request, SUCCESS_MSG)
                    return HttpResponseRedirect(DASHBOARD_URI)
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
    initial['cashout_markup_in_bps'] = merchant.get_cashout_percent_markup()
    initial['cashin_markup_in_bps'] = merchant.get_cashin_percent_markup()
    initial['max_mbtc_shopper_purchase'] = merchant.max_mbtc_shopper_purchase
    initial['max_mbtc_shopper_sale'] = merchant.max_mbtc_shopper_sale
    bitcoin_form = BitcoinInfoForm(initial=initial)
    return {
        'user': user,
        'merchant': merchant,
        'bitcoin_form': bitcoin_form,
        'dest_address': dest_address,
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
    website_obj = merchant.get_website_obj()
    if website_obj:
        initial['website'] = website_obj.url

    # biz hours, so WET :(
    hours_formatted = merchant.get_hours_formatted()

    # if hours_formatted.get(1):
    #     initial['monday_open'] = hours_formatted.get(1)['from_time'].hour
    #     initial['monday_close'] = hours_formatted.get(1)['to_time'].hour
    # if hours_formatted.get(2):
    #     initial['tuesday_open'] = hours_formatted.get(2)['from_time'].hour
    #     initial['tuesday_close'] = hours_formatted.get(2)['to_time'].hour
    # if hours_formatted.get(3):
    #     initial['wednesday_open'] = hours_formatted.get(3)['from_time'].hour
    #     initial['wednesday_close'] = hours_formatted.get(3)['to_time'].hour
    # if hours_formatted.get(4):
    #     initial['thursday_open'] = hours_formatted.get(4)['from_time'].hour
    #     initial['thursday_close'] = hours_formatted.get(4)['to_time'].hour
    # if hours_formatted.get(5):
    #     initial['friday_open'] = hours_formatted.get(5)['from_time'].hour
    #     initial['friday_close'] = hours_formatted.get(5)['to_time'].hour
    # if hours_formatted.get(6):
    #     initial['saturday_open'] = hours_formatted.get(6)['from_time'].hour
    #     initial['saturday_close'] = hours_formatted.get(6)['to_time'].hour
    # if hours_formatted.get(7):
    #     initial['sunday_open'] = hours_formatted.get(7)['from_time'].hour
    #     initial['sunday_close'] = hours_formatted.get(7)['to_time'].hour

    hours_to_value = {}
    for i in range(1, 24):
        hours_to_value[datetime.time(i)] = i
    hours_form_initial = {}
    days_to_value = [[1, 'mon'], [2, 'tues'], [3, 'wed'], [4, 'thurs'], [5, 'fri'], [6, 'sat'], [7, 'sun']]
    for num, value in days_to_value:
        if hours_formatted.get(num):
            hours_form_initial[value] = {}
            day = hours_formatted.get(num)
            if day['from_time'] == 'closed':
                hours_form_initial[value] = {'closed': True}
            else:
                hours_form_initial[value] = {
                    'closed': False,
                    'open': hours_to_value[day['from_time']],
                    'close': hours_to_value[day['to_time']],
                }

    return {
        'user': user,
        'merchant': merchant,
        'transactions': transactions,
        'personal_form': OwnerInfoForm(initial=initial),
        'merchant_form': MerchantInfoForm(initial=initial),
        # 'hours_form': BusinessHoursForm(initial=initial),
        'biz_hours': hours_formatted,
        'hours_form_initial': hours_form_initial
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

        data = request.POST
        hours = []

        if 'closed_mon' in data and data['closed_mon'] == 'on':
            hours.append((1, 'closed', 'closed'))
        else:
            mon_open = int(data['mon_open'])
            mon_close = int(data['mon_close'])
            if mon_open > 0 and mon_close > 0:
                hours.append((1, datetime.time(mon_open), datetime.time(mon_close)))

        if 'closed_tues' in data and data['closed_tues'] == 'on':
            hours.append((2, 'closed', 'closed'))
        else:
            tues_open = int(data['tues_open'])
            tues_close = int(data['tues_close'])
            if tues_open > 0 and tues_close > 0:
                hours.append((2, datetime.time(tues_open), datetime.time(tues_close)))

        if 'closed_wed' in data and data['closed_wed'] == 'on':
            hours.append((3, 'closed', 'closed'))
        else:
            wed_open = int(data['wed_open'])
            wed_close = int(data['wed_close'])
            if wed_open > 0 and wed_close > 0:
                hours.append((3, datetime.time(wed_open), datetime.time(wed_close)))

        if 'closed_thurs' in data and data['closed_thurs'] == 'on':
            hours.append((4, 'closed', 'closed'))
        else:
            thurs_open = int(data['thurs_open'])
            thurs_close = int(data['thurs_close'])
            if thurs_open > 0 and thurs_close > 0:
                hours.append((4, datetime.time(thurs_open), datetime.time(thurs_close)))

        if 'closed_fri' in data and data['closed_fri'] == 'on':
            hours.append((5, 'closed', 'closed'))
        else:
            fri_open = int(data['fri_open'])
            fri_close = int(data['fri_close'])
            if fri_open > 0 and fri_close > 0:
                hours.append((5, datetime.time(fri_open), datetime.time(fri_close)))

        if 'closed_sat' in data and data['closed_sat'] == 'on':
            hours.append((6, 'closed', 'closed'))
        else:
            sat_open = int(data['sat_open'])
            sat_close = int(data['sat_close'])
            if sat_open > 0 and sat_close > 0:
                hours.append((6, datetime.time(sat_open), datetime.time(sat_close)))

        if 'closed_sun' in data and data['closed_sun'] == 'on':
            hours.append((7, 'closed', 'closed'))
        else:
            sun_open = int(data['sun_open'])
            sun_close = int(data['sun_close'])
            if sun_open > 0 and sun_close > 0:
                hours.append((6, datetime.time(sun_open), datetime.time(sun_close)))

        merchant = user.get_merchant()
        merchant.set_hours(hours)
        msg = _('Your business hours have been updated')
        messages.success(request, msg)
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
            merchant.max_mbtc_shopper_sale = form.cleaned_data['max_mbtc_shopper_sale']
            merchant.max_mbtc_shopper_purchase = form.cleaned_data['max_mbtc_shopper_purchase']
            # merchant.basis_points_markup = form.cleaned_data['btc_markup'] * 100
            merchant.cashin_markup_in_bps = form.cleaned_data['cashin_markup_in_bps'] * 100
            merchant.cashout_markup_in_bps = form.cleaned_data['cashout_markup_in_bps'] * 100
            merchant.save()
            merchant.set_destination_address(
                    dest_address=form.cleaned_data['btc_address'],
                    credential_used=None)

            messages.success(request, _('Your bitcoin info has been updated'))
            return HttpResponseRedirect(reverse_lazy('merchant_settings'))

    messages.warning(request, _('Your bitcoin info was not updated'))
    return HttpResponseRedirect(reverse_lazy('merchant_settings'))


@login_required
@render_to('merchants/password_prompt.html')
def password_prompt(request):
    user = request.user
    merchant = user.get_merchant()
    if not merchant or not merchant.has_finished_registration():
        return HttpResponseRedirect(reverse_lazy('register_router'))

    initial = None
    if request.method == 'GET':
        if request.GET.get('next'):
            initial = {'redir_path': request.GET.get('next')}

    form = PasswordConfirmForm(user=user, initial=initial)
    if request.method == 'POST':
        form = PasswordConfirmForm(user=user, data=request.POST)
        if form.is_valid():
            request.session['last_password_validation'] = now().ctime()
            redir_path = form.cleaned_data['redir_path']
            if redir_path:
                # add leading/trailling slashes
                redir_path = '/%s/' % redir_path
            else:
                redir_path = reverse_lazy('merchant_transactions')
            return HttpResponseRedirect(redir_path)
    return {
        'form': form,
        'user': user,
        'merchant': merchant,
        }
