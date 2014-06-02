from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape

from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from merchants.forms import (LoginForm, AccountRegistrationForm,
        BitcoinRegistrationForm, PersonalInfoRegistrationForm,
        MerchantInfoRegistrationForm)
from merchants.models import AppUser, Merchant
from bitcash.decorators import confirm_registration_eligible

from services.models import WebHook


@render_to('login.html')
def login_request(request):
    form = LoginForm()

    WebHook.create_webhook(request, WebHook.BCI_PAYMENT_FORWARDED)

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            # Log in user
            username = form.cleaned_data['username'].lower()
            password = form.cleaned_data['password']

            user_found = get_object_or_None(AppUser, username=username)
            if user_found:
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)

                    # Log the login

                    msg = 'Welcome <b>%s</b>,' % user.username
                    msg += ' you are now logged in.'
                    messages.success(request, msg, extra_tags='safe')

                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    msg = "Sorry, that's not the right password for "
                    msg += '<b>%s</b>.' % escape(username)
                    messages.warning(request, msg, extra_tags='safe')
            else:
                msg = "No account found for <b>%s</b>." % escape(username)
                messages.warning(request, msg, extra_tags='safe')

    return {'form': form}


def logout_request(request):
    " Log a user out using Django's logout function and redirect them "
    logout(request)
    msg = "You Are Now Logged Out"
    messages.success(request, msg)
    return HttpResponseRedirect(reverse_lazy('login_request'))


def register_router(request):
    user = request.user
    if not user.is_authenticated():  # if user is not authenticated
        return HttpResponsePermanentRedirect(reverse_lazy('register_account'))

    # onboarding steps
    reg_step = user.get_registration_step()
    if reg_step == 0:
        return HttpResponseRedirect(reverse_lazy('register_personal'))
    elif reg_step == 1:
        return HttpResponseRedirect(reverse_lazy('register_merchant'))
    elif reg_step == 2:
        return HttpResponseRedirect(reverse_lazy('register_bitcoins'))

    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


@render_to('register_account.html')
def register_account(request):
    user = request.user
    form = AccountRegistrationForm()
    if request.method == 'POST':
        form = AccountRegistrationForm(data=request.POST)
        if form.is_valid():

            password = form.cleaned_data['password']

            # other fields
            email = form.cleaned_data['email']

            # create user
            user = AppUser.objects.create_user(
                    email,
                    email=email,
                    password=password
                    )
            user_to_login = authenticate(username=email, password=password)
            login(request, user_to_login)
            return HttpResponseRedirect(reverse_lazy('register_personal'))
    return {'form': form, 'user': user}


@login_required
@confirm_registration_eligible
@render_to('register_personal.html')
def register_personal(request):
    user = request.user
    initial = {}
    if user.full_name:
        initial['full_name'] = user.full_name
        initial['phone_num'] = user.phone_num
        initial['phone_country'] = user.phone_num_country
    else:
        initial['phone_country'] = 'USA'
    form = PersonalInfoRegistrationForm(initial=initial)
    if request.method == 'POST':
        form = PersonalInfoRegistrationForm(data=request.POST)
        if form.is_valid():

            full_name = form.cleaned_data['full_name']
            phone_num = form.cleaned_data['phone_num']
            phone_country = form.cleaned_data['phone_country']

            user.full_name = full_name
            user.phone_num = phone_num
            user.phone_num_country = phone_country
            user.save()

            return HttpResponseRedirect(reverse_lazy('register_merchant'))
    return {'form': form, 'user': user}


@login_required
@confirm_registration_eligible
@render_to('register_merchant.html')
def register_merchant(request):
    user = request.user
    merchant = user.get_merchant()
    initial = {}
    if merchant:
        initial['country'] = merchant.country
        initial['business_name'] = merchant.business_name
        initial['address_1'] = merchant.address_1
        initial['address_2'] = merchant.address_2
        initial['city'] = merchant.city
        initial['state'] = merchant.state
        initial['zip_code'] = merchant.zip_code
        initial['country'] = merchant.country
        initial['phone_num'] = merchant.phone_num
    else:
        initial['country'] = user.phone_num_country
    form = MerchantInfoRegistrationForm(initial=initial)
    if request.method == 'POST':
        form = MerchantInfoRegistrationForm(data=request.POST)
        if form.is_valid():

            business_name = form.cleaned_data['business_name']
            address_1 = form.cleaned_data['address_1']
            address_2 = form.cleaned_data['address_2']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            country = form.cleaned_data['country']
            zip_code = form.cleaned_data['zip_code']
            phone_num = form.cleaned_data['phone_num']

            if merchant:
                merchant.business_name = business_name
                merchant.address_1 = address_1
                merchant.address_2 = address_2
                merchant.city = city
                merchant.state = state
                merchant.country = country
                merchant.zip_code = zip_code
                merchant.phone_num = phone_num
                merchant.save()
            else:
                merchant = Merchant.objects.create(
                    app_user=user,
                    business_name=business_name,
                    address_1=address_1,
                    address_2=address_2,
                    city=city,
                    state=state,
                    country=country,
                    zip_code=zip_code,
                    phone_num=phone_num,
                )

            return HttpResponseRedirect(reverse_lazy('register_bitcoins'))
    return {'form': form, 'user': user}


@login_required
# @confirm_registration_eligible
@render_to('register_bitcoins.html')
def register_bitcoins(request):
    user = request.user
    merchant = user.get_merchant()
    initial = {}
    initial['btc_markup'] = merchant.basis_points_markup / 100.0
    if merchant.currency_code:
        initial['currency_code'] = merchant.currency_code
    if merchant.has_destination_address():
        initial['btc_address'] = merchant.get_destination_address()
    form = BitcoinRegistrationForm(initial=initial)
    if request.method == 'POST':
        form = BitcoinRegistrationForm(data=request.POST)
        if form.is_valid():
            currency_code = form.cleaned_data['currency_code']
            btc_address = form.cleaned_data['btc_address']
            basis_points_markup = form.cleaned_data['btc_markup']
            merchant.currency_code = currency_code
            merchant.basis_points_markup = basis_points_markup * 100
            merchant.save()

            merchant.set_destination_address(btc_address)

            return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
    return {'form': form, 'user': user}


@login_required
@render_to('merchant_settings.html')
def merchant_settings(request):
    user = request.user
    merchant = user.get_merchant()
    dest_address = merchant.get_destination_address()
    initial = {}

    initial['currency_code'] = merchant.currency_code
    initial['btc_address'] = dest_address.b58_address
    initial['btc_markup'] = merchant.basis_points_markup / 100.0
    bitcoin_form = BitcoinRegistrationForm(initial=initial)
    return {
        'user': user,
        'merchant': merchant,
        'on_admin_page': True,
        'bitcoin_form': bitcoin_form,
        'dest_address': dest_address
    }


@login_required
@render_to('merchant_profile.html')
def merchant_profile(request):
    user = request.user
    merchant = user.get_merchant()
    transactions = merchant.get_all_transactions()
    initial = {}
    initial['full_name'] = user.full_name
    initial['phone_num'] = user.phone_num
    initial['phone_country'] = user.phone_num_country

    initial['business_name'] = merchant.business_name
    initial['address_1'] = merchant.address_1
    initial['address_2'] = merchant.address_2
    initial['city'] = merchant.city
    initial['state'] = merchant.state
    initial['zip_code'] = merchant.zip_code
    initial['country'] = merchant.country
    initial['phone_num'] = merchant.phone_num

    initial['currency_code'] = merchant.currency_code
    initial['btc_address'] = merchant.get_destination_address()
    initial['btc_markup'] = merchant.basis_points_markup / 100.0

    personal_form = PersonalInfoRegistrationForm(initial=initial)
    merchant_form = MerchantInfoRegistrationForm(initial=initial)
    bitcoin_form = BitcoinRegistrationForm(initial=initial)
    return {
        'user': user,
        'merchant': merchant,
        'transactions': transactions,
        'on_admin_page': True,
        'personal_form': personal_form,
        'merchant_form': merchant_form,
        'bitcoin_form': bitcoin_form
    }


@login_required
@render_to('merchant_transactions.html')
def transactions(request):
    user = request.user
    merchant = user.get_merchant()
    transactions = merchant.get_all_transactions()
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
        form = PersonalInfoRegistrationForm(data=request.POST)
        if form.is_valid():

            full_name = form.cleaned_data['full_name']
            phone_num = form.cleaned_data['phone_num']
            phone_country = form.cleaned_data['phone_country']

            user.full_name = full_name
            user.phone_num = phone_num
            user.phone_num_country = phone_country
            user.save()
            msg = 'Your profile has been updated'
            messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('merchant_profile'))


@login_required
def edit_merchant_info(request):
    user = request.user
    merchant = user.get_merchant()
    if request.method == 'POST':
        form = MerchantInfoRegistrationForm(data=request.POST)
        if form.is_valid():

            business_name = form.cleaned_data['business_name']
            address_1 = form.cleaned_data['address_1']
            address_2 = form.cleaned_data['address_2']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            country = form.cleaned_data['country']
            zip_code = form.cleaned_data['zip_code']
            phone_num = form.cleaned_data['phone_num']

            if merchant:
                merchant.business_name = business_name
                merchant.address_1 = address_1
                merchant.address_2 = address_2
                merchant.city = city
                merchant.state = state
                merchant.country = country
                merchant.zip_code = zip_code
                merchant.phone_num = phone_num
                merchant.save()

                msg = 'Your profile has been updated'
                messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('merchant_profile'))


@login_required
def edit_bitcoin_info(request):
    user = request.user
    merchant = user.get_merchant()
    if request.method == 'POST':
        form = BitcoinRegistrationForm(data=request.POST)
        if form.is_valid():
            currency_code = form.cleaned_data['currency_code']
            btc_address = form.cleaned_data['btc_address']
            markup = form.cleaned_data['btc_markup']
            if merchant:
                merchant.currency_code = currency_code
                merchant.set_destination_address(btc_address)
                merchant.basis_points_markup = markup * 100
                merchant.save()
                msg = 'Your profile has been updated'
                messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('merchant_settings'))
