from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.html import escape
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from merchants.models import Merchant
from users.models import AuthUser, LoggedLogin

from merchants.forms import (LoginForm, MerchantRegistrationForm,
        BitcoinRegistrationForm, PersonalInfoRegistrationForm,
        MerchantInfoRegistrationForm)


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

                    msg = 'Welcome <b>%s</b>,' % user.username
                    msg += ' you are now logged in.'
                    messages.success(request, msg, extra_tags='safe')

                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    msg = "Sorry, that's not the right password for "
                    msg += '<b>%s</b>.' % escape(email)
                    messages.warning(request, msg, extra_tags='safe')
            else:
                msg = "No account found for <b>%s</b>." % escape(email)
                messages.warning(request, msg, extra_tags='safe')

    elif request.method == 'GET':
        email = request.GET.get('e')
        if email:
            form = LoginForm(initial={'email': email})

    return {'form': form}


def logout_request(request):
    " Log a user out using Django's logout function and redirect them "
    logout(request)
    msg = "You Are Now Logged Out"
    messages.success(request, msg)
    return HttpResponseRedirect(reverse_lazy('login_request'))


@render_to('merchants/register.html')
def register_merchant(request):
    user = request.user
    initial = {'btc_markup': 2.0}
    form = MerchantRegistrationForm(initial=initial)
    form_valid = True  # used to decide whether we run the JS or not
    if request.method == 'POST':
        form = MerchantRegistrationForm(data=request.POST)
        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            full_name = form.cleaned_data['full_name']
            business_name = form.cleaned_data['business_name']
            country = form.cleaned_data['country']
            currency_code = form.cleaned_data['currency_code']
            btc_address = form.cleaned_data['btc_address']
            basis_points_markup = form.cleaned_data['btc_markup']

            existing_user = get_object_or_None(AuthUser, username=email)
            if existing_user:
                login_url = '%s?e=%s' % (reverse_lazy('login_request'), existing_user.email)
                msg = 'That email is already taken, do you want to '
                msg += '<a href="%s">login</a>?' % login_url
                messages.warning(request, msg, extra_tags='safe')
            else:
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
                        basis_points_markup=basis_points_markup * 100,
                        )
                merchant.set_destination_address(btc_address)

                # login user
                user_to_login = authenticate(username=email, password=password)
                login(request, user_to_login)

                # Log the login
                LoggedLogin.record_login(request)

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))

        else:
            form_valid = False

    elif request.method == 'GET':
        email = request.GET.get('e')
        if email:
            initial['email'] = email
            form = MerchantRegistrationForm(initial=initial)

    return {'form': form, 'user': user, 'form_valid': form_valid}


@login_required
@render_to('merchants/settings.html')
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
@render_to('merchants/profile.html')
def merchant_profile(request):
    user = request.user
    merchant = user.get_merchant()
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

    personal_form = PersonalInfoRegistrationForm(initial=initial)
    merchant_form = MerchantInfoRegistrationForm(initial=initial)
    return {
        'user': user,
        'merchant': merchant,
        'transactions': transactions,
        'on_admin_page': True,
        'personal_form': personal_form,
        'merchant_form': merchant_form
    }


@login_required
@render_to('merchants/transactions.html')
def merchant_transactions(request):
    user = request.user
    merchant = user.get_merchant()
    transactions = merchant.get_all_forwarding_transactions()
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
            email = form.cleaned_data['email']
            phone_num = form.cleaned_data['phone_num']
            phone_country = form.cleaned_data['phone_country']

            user.full_name = full_name
            user.phone_num = phone_num
            user.phone_num_country = phone_country
            user.email = email
            user.username = email
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
