from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.contrib import messages
from django.utils.html import escape

from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from business.forms import *
from business.models import AppUser, Business
from bitcoins.models import BTCAddress


@render_to('login.html')
def login_request(request):
    form = LoginForm()

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
            user = AppUser.objects.create_user(email,
                email=email,
                password=password
            )
            user_to_login = authenticate(username=email, password=password)
            login(request, user_to_login)
            return HttpResponseRedirect(reverse_lazy('register_personal'))
    return {'form': form, 'user':user}


@login_required
@render_to('register_personal.html')
def register_personal(request):
    user = request.user
    form = PersonalInfoRegistrationForm()
    if request.method == 'POST':
        form = PersonalInfoRegistrationForm(data=request.POST)
        if form.is_valid():

            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_num = form.cleaned_data['phone_num']

            user.first_name = first_name
            user.last_name = last_name
            user.phone_num = phone_num
            user.save()

            return HttpResponseRedirect(reverse_lazy('register_business'))
    return {'form': form, 'user': user}


@login_required
@render_to('register_business.html')
def register_business(request):
    user = request.user
    form = BusinessInfoRegistrationForm()
    if request.method == 'POST':
        form = BusinessInfoRegistrationForm(data=request.POST)
        if form.is_valid():

            business_name = form.cleaned_data['business_name']
            address_1 = form.cleaned_data['address_1']
            address_2 = form.cleaned_data['address_2']
            city = form.cleaned_data['city']
            country = form.cleaned_data['country']
            zip_code = form.cleaned_data['zip_code']
            phone_num = form.cleaned_data['phone_num']
            hours = form.cleaned_data['hours']
            currency_code = form.cleaned_data['currency_code']

            business = Business.objects.create(
                app_user=user,
                business_name=business_name,
                address_1=address_1,
                address_2=address_2,
                city=city,
                country=country,
                zip_code=zip_code,
                phone_num=phone_num,
                hours=hours,
                currency_code=currency_code
            )

            address = BTCAddress.objects.create(
                generated_at=now(),
                b58_address='1FXK3Qeu6ouf2haDXUCttWRHH4SLdRoFhA',
                business=business,
            )

            return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
    return {'form': form, 'user':user}


@login_required
@render_to('business_dash.html')
def business_dash(request):
    user = request.user
    business = user.get_business()
    transactions = business.get_all_transactions()
    return {
        'user': user,
        'business': business,
        'transactions': transactions,
        'on_admin_page': True
    }
