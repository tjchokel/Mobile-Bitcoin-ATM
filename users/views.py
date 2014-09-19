from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils.timezone import now
from django.contrib.auth import authenticate, login

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from users.models import FutureShopper, AuthUser, EmailAuthToken, LoggedLogin
from merchants.models import Merchant

from users.forms import CustomerRegistrationForm, ContactForm, ChangePWForm, RequestNewPWForm, SetPWForm

from emails.trigger import send_and_log

from datetime import timedelta

from utils import SATOSHIS_PER_BTC
import requests
import json


@render_to('index.html')
def home(request):
    user = request.user
    if user.is_authenticated():
        merchant = user.get_merchant()
        if merchant:
            if merchant.has_finished_registration():
                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
            else:
                return HttpResponseRedirect(reverse_lazy('register_router'))
    merchants_for_map = Merchant.objects.filter(longitude_position__isnull=False, latitude_position__isnull=False)
    form = CustomerRegistrationForm()
    if request.method == 'POST':
        form = CustomerRegistrationForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            country = form.cleaned_data['country']
            city = form.cleaned_data['city']
            FutureShopper.objects.create(
                    email=form.cleaned_data['email'],
                    city=form.cleaned_data['city'],
                    country=form.cleaned_data['country'],
            )
            msg = _("Thanks! We'll email you when new businesses near you sign up.")
            messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('home'))
        else:
            msg = _("There was an error with your submission. Please try again.")
            messages.warning(request, msg, extra_tags='safe')

    return {
            'merchants_for_map': merchants_for_map,
            'form': form,
           }


@render_to('fixed_pages/contact.html')
def contact(request):
    if request.user.is_authenticated():
        initial = {
                'name': request.user.full_name,
                'email': request.user.username,
                }
        form = ContactForm(initial=initial)
    else:
        form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            name = form.cleaned_data['name']
            message = form.cleaned_data['message']
            body_context = {
                    'email': email,
                    'name': name,
                    'message': message,
                    }
            send_and_log(
                subject='CoinSafe Support Message From %s' % name,
                body_template='admin/contact_form.html',
                to_merchant=None,
                to_email='support@coinsafe.com',
                to_name='CoinSafe Support',
                body_context=body_context,
                replyto_name=name,
                replyto_email=email,
                )
            msg = _("Message Received! We'll get back to you soon.")
            messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('home'))

    return {'form': form}


@login_required
@render_to('users/change_pw.html')
def change_password(request):
    user = request.user
    form = ChangePWForm(user=user)
    if request.method == 'POST':
        form = ChangePWForm(user=user, data=request.POST)
        if form.is_valid():
            new_pw = form.cleaned_data['newpassword']
            user.set_password(new_pw)
            user.save()

            msg = _('Your password has been changed.')
            messages.success(request, msg, extra_tags='safe')

            return HttpResponseRedirect(reverse_lazy('home'))

    return {
            'form': form,
            'merchant': user.get_merchant(),
            }


@render_to('users/request_new_password.html')
def request_new_password(request):
    if request.user.is_authenticated():
        msg = _('You are already logged in. You must <a href="/logout/">logout</a> before you can reset your password.')
        messages.error(request, msg, extra_tags='safe')

    form = RequestNewPWForm()
    show_form = True
    if request.method == 'POST':
        form = RequestNewPWForm(data=request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            existing_user = get_object_or_None(AuthUser, username=email.lower())
            if existing_user:
                new_token = existing_user.create_email_auth_token(request=request)
                new_token.send_pwreset_email()
                show_form = False

            else:
                msg = _('Sorry, no user found with that email address. Please <a href="/contact/">contact us</a> if this is a mistake.')
                messages.error(request, msg, extra_tags='safe')
    elif request.method == 'GET':
        email = request.GET.get('e')
        if email:
            form = RequestNewPWForm(initial={'email': email})

    return {'form': form, 'show_form': show_form}


@render_to('users/reset_password.html')
def reset_password(request, verif_key):
    if request.user.is_authenticated():
        msg = _('''You're already logged in. You must <a href="/logout/">logout</a> before you can reset your password.''')
        messages.error(request, msg, extra_tags='safe')
        return HttpResponseRedirect(reverse_lazy('home'))

    ea_token = get_object_or_None(EmailAuthToken, verif_key=verif_key)
    if not ea_token:
        msg = _('Sorry, that link is not valid. Please <a href="/contact/">contact us</a> if this is a mistake.')
        messages.warning(request, msg, extra_tags='safe')
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    if now() > ea_token.key_expires_at:
        msg = _('Sorry, that link was already used. Please generate a new one.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    if ea_token.key_used_at:
        if now() - ea_token.key_used_at < timedelta(minutes=15):
            request.session['email_auth_token_id'] = ea_token.id
            return HttpResponseRedirect(reverse_lazy('set_new_password'))
        else:
            msg = _('Sorry, that link was already used. Please generate a new one.')
            messages.warning(request, msg)
            return HttpResponseRedirect(reverse_lazy('request_new_password'))
    else:
        ea_token.key_used_at = now()
        ea_token.save()
        request.session['email_auth_token_id'] = ea_token.id
        return HttpResponseRedirect(reverse_lazy('set_new_password'))


@render_to('users/set_new_password.html')
def set_new_password(request):
    if request.user.is_authenticated():
        msg = _('''You're already logged in. You must <a href="/logout/">logout</a> before you can reset your password.''')
        messages.error(request, msg, extra_tags='safe')
        return HttpResponseRedirect(reverse_lazy('home'))

    # none of these things *should* ever happen, hence the cryptic error message (to figure out how that's possible)
    email_auth_token_id = request.session.get('email_auth_token_id')
    if not email_auth_token_id:
        msg = _('Token cookie not found. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    ea_token = get_object_or_None(EmailAuthToken, id=email_auth_token_id)
    if not ea_token:
        msg = _('Token not found. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    if ea_token.key_deleted_at:
        msg = _('Token deleted. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password')+'?e='+ea_token.auth_user.email)
    if not ea_token.key_used_at:
        msg = _('Site error. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password')+'?e='+ea_token.auth_user.email)
    if now() - ea_token.key_used_at > timedelta(minutes=15):
        msg = _('Time limit expired. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password')+'?e='+ea_token.auth_user.email)
    else:
        # We're good to go!
        form = SetPWForm()
        if request.method == 'POST':
            form = SetPWForm(data=request.POST)
            if form.is_valid():
                new_pw = form.cleaned_data['newpassword']
                user = ea_token.auth_user
                user.set_password(new_pw)
                user.save()

                # login user
                user_to_login = authenticate(username=user.username, password=new_pw)
                login(request, user_to_login)

                LoggedLogin.record_login(request)

                # delete the token from the session
                del request.session['email_auth_token_id']

                merchant = user.get_merchant()
                if merchant:
                    api_cred = merchant.get_api_credential()
                    if api_cred:
                        try:
                            if api_cred.get_balance() > SATOSHIS_PER_BTC:
                                merchant.disable_all_credentials()
                                # TODO: poor UX, but let's wait until we actually have people doing this
                                msg = _('Your API credentials were unlinked from your CoinSafe account for safety, please link your wallet again in order to sell bitcoin to customers.')
                                messages.success(request, msg)
                        except Exception as e:
                            # TODO: log these somewhere when people start using this feature
                            print 'Error was: %s' % e

                # Mark this + all other tokens for that user as expired
                ea_token.expire_outstanding_tokens()

                msg = _('Password succesfully updated.')
                messages.success(request, msg)

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))

    return {'form': form}


def city_autocomplete(request):
    " Returns AJAX payload of cities matching search term"
    AUTOCOMPLETE_URL = "http://gd.geobytes.com/AutoCompleteCity"
    city = request.GET.get('q')
    country = request.GET.get('filter')
    params = {'q': city}
    if country:
        params['filter'] = country
    r = requests.get(AUTOCOMPLETE_URL, params=params)
    json_dict = {'cities': r.content}
    json_response = json.dumps(json_dict)
    return HttpResponse(json_response, content_type='application/json')
