from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters
from django.utils.timezone import now
from django.contrib.auth import authenticate, login

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from bitcoins.models import BTCTransaction, ShopperBTCPurchase
from shoppers.models import Shopper
from users.models import FutureShopper, AuthUser, EmailAuthToken, LoggedLogin
from merchants.models import Merchant

from shoppers.forms import ShopperInformationForm, BuyBitcoinForm, NoEmailBuyBitcoinForm, ConfirmPasswordForm
from users.forms import CustomerRegistrationForm, ContactForm, ChangePWForm, RequestNewPWForm, SetPWForm

from emails.trigger import send_and_log, send_admin_email

from datetime import timedelta

from utils import SATOSHIS_PER_BTC


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

    return {'merchants_for_map': merchants_for_map}


@sensitive_variables('password', 'password_form')
@sensitive_post_parameters('password', )
@login_required
@render_to('customer_dash/main.html')
def customer_dashboard(request):
    user = request.user
    if user.is_superuser:
        return HttpResponseRedirect(reverse_lazy('admin:index'))

    merchant = user.get_merchant()
    if not merchant or not merchant.has_destination_address():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    transactions, shopper = None, None
    forwarding_address_obj = merchant.get_latest_forwarding_obj()
    btc_purchase_request = merchant.get_bitcoin_purchase_request()

    if btc_purchase_request and btc_purchase_request.is_cancelled():
        # Defensive check on cash-in, can't think of when this *should* happen
        msg = _('Sorry, that request was cancelled. Please contact us if that was not intentional.')
        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))

    if merchant.has_valid_coinbase_credentials():
        buy_form = BuyBitcoinForm(initial={'email_or_btc_address': '1'}, merchant=merchant)
    else:
        buy_form = NoEmailBuyBitcoinForm(merchant=merchant)
    password_form = ConfirmPasswordForm(user=user)
    shopper_form = ShopperInformationForm(initial={'phone_country': merchant.country})
    override_confirmation_form = ConfirmPasswordForm(user=user)
    show_buy_modal, show_confirm_purchase_modal, show_override_confirmations_modal = 'false', 'false', 'false'
    if forwarding_address_obj:
        # In case of refreshing the page later
        # Will be None on first use and be overwritten below
        shopper = forwarding_address_obj.shopper
        transactions = forwarding_address_obj.get_all_forwarding_transactions()
    if request.method == 'POST':
        # if submitting a buy bitcoin form
        if 'amount' in request.POST:
            if merchant.has_valid_coinbase_credentials():
                buy_form = BuyBitcoinForm(data=request.POST, merchant=merchant)
            else:
                buy_form = NoEmailBuyBitcoinForm(data=request.POST, merchant=merchant)
            if buy_form.is_valid():
                if merchant.has_valid_coinbase_credentials():
                    email_or_btc_address = buy_form.cleaned_data['email_or_btc_address']
                else:
                    email_or_btc_address = None
                amount = buy_form.cleaned_data['amount']
                email = buy_form.cleaned_data['email']
                btc_address = buy_form.cleaned_data['btc_address']
                # Create shopper object
                shopper = Shopper.objects.create(
                    email=email,
                )

                credential = merchant.get_valid_api_credential()
                # if sending to email
                if email_or_btc_address and email_or_btc_address == '1':
                    ShopperBTCPurchase.objects.create(
                        merchant=merchant,
                        shopper=shopper,
                        fiat_amount=amount,
                        credential=credential,
                    )
                else:
                    ShopperBTCPurchase.objects.create(
                        merchant=merchant,
                        shopper=shopper,
                        fiat_amount=amount,
                        b58_address=btc_address,
                        credential=credential,
                    )

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
            else:
                show_buy_modal = 'true'
        # if submitting shopper form
        elif 'name' in request.POST:
            shopper_form = ShopperInformationForm(data=request.POST)
            if shopper_form.is_valid():

                name = shopper_form.cleaned_data['name']
                email = shopper_form.cleaned_data['email']
                phone_num = shopper_form.cleaned_data['phone_num']

                # Create shopper object
                shopper = Shopper.objects.create(
                    name=name,
                    email=email,
                    phone_num=phone_num,
                )

                forwarding_address_obj.shopper = shopper
                forwarding_address_obj.save()

                # Fetch existing TXs if they exist
                existing_txns = BTCTransaction.objects.filter(
                        forwarding_address=forwarding_address_obj,
                        destination_address__isnull=True)

                # If we have an TX then send a notification to the shopper
                # They are probably unconfirmed but they may be confirmed by now
                for existing_txn in existing_txns:
                    if existing_txn.met_minimum_confirmation_at:
                        existing_txn.send_shopper_txconfirmed_email()
                        existing_txn.send_shopper_txconfirmed_sms()
                    else:
                        existing_txn.send_shopper_newtx_email()
                        existing_txn.send_shopper_newtx_sms()

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
        # if submitting password confirmation form
        elif 'password' in request.POST:
            if btc_purchase_request:
                # cash in scenario, sending bitcoin to shopper
                password_form = ConfirmPasswordForm(user=user, data=request.POST)
                if password_form.is_valid():
                    btc_purchase_request_updated, api_call, err_str = btc_purchase_request.pay_out_bitcoin(send_receipt=True)
                    if err_str:
                        if api_call:
                            api_call.send_admin_btcpurchase_error_email(btc_purchase_request_updated)
                        else:
                            # These errors are OK to include in plaintext emails, they messages are written by us
                            body_context = {
                                    'coinsafe_err_str': err_str,
                                    'shopper_request_url': reverse_lazy(
                                        'admin:bitcoins_shopperbtcpurchase_change',
                                        args=(btc_purchase_request.id, )
                                        )
                                    }
                            send_admin_email(
                                    body_template='btc_purchase_not_attempted_notification.html',
                                    subject='Non API Error for Shopper BTC Purchase Request %s' % btc_purchase_request.id,
                                    body_context=body_context,
                                    )
                        show_confirm_purchase_modal = 'false'
                        msg = _('Bitcoin sending failed. The API returned the following error: %s' % err_str)
                        messages.warning(request, msg)
                        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                    else:
                        msg = _('Success! Your bitcoin is being sent. A receipt will be emailed to %s' % btc_purchase_request.shopper.email)
                        messages.success(request, msg)
                        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    show_confirm_purchase_modal = 'true'
            else:
                # cash out scenario, overriding required confirmations
                override_confirmation_form = ConfirmPasswordForm(user=user, data=request.POST)
                if override_confirmation_form.is_valid():
                    if transactions:
                        # Possible corner case where a person could have two
                        # tabs open and override the transaction in the other tab.
                        # Then they wouldn't have any transactions in this tab
                        for transaction in transactions:
                            # Having a transactions array is confusing, but it's
                            # possible a person would send BTC in multiple transactions
                            transaction.set_merchant_confirmation_override()
                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    show_override_confirmations_modal = 'true'

    return {
        'user': user,
        'merchant': merchant,
        'current_address': forwarding_address_obj,
        'transactions': transactions,
        'shopper': shopper,
        'buy_request': btc_purchase_request,
        'password_form': password_form,
        'shopper_form': shopper_form,
        'buy_form': buy_form,
        'override_confirmation_form': override_confirmation_form,
        'show_buy_modal': show_buy_modal,
        'show_confirm_purchase_modal': show_confirm_purchase_modal,
        'show_override_confirmations_modal': show_override_confirmations_modal,
    }


@render_to('register_customer.html')
def register_customer(request):
    form = CustomerRegistrationForm()
    if request.method == 'POST':
        form = CustomerRegistrationForm(data=request.POST)
        if form.is_valid():
            # create customer
            FutureShopper.objects.create(
                    email=form.cleaned_data['email'],
                    city=form.cleaned_data['city'],
                    country=form.cleaned_data['country'],
                    intention=form.cleaned_data['intention'],
            )
            msg = _("Thanks! We'll email you when new businesses near you sign up.")
            messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('home'))

    return {'form': form}


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
        messages.error(request, msg)

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
        if ea_token.key_used_at - timedelta(minutes=15) < now():
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

    email_auth_token_id = request.session.get('email_auth_token_id')
    if not email_auth_token_id:
        msg = _('Access denied. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    ea_token = get_object_or_None(EmailAuthToken, id=email_auth_token_id)

    if not ea_token:
        msg = _('Access denied. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    if not ea_token.key_used_at:
        msg = _('Site error. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
    if ea_token.key_used_at + timedelta(minutes=15) < now():
        msg = _('Time limit expired. Please generate a new link.')
        messages.warning(request, msg)
        return HttpResponseRedirect(reverse_lazy('request_new_password'))
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
                    api_cred = merchant.get_valid_api_credential()
                    if api_cred.get_balance() > SATOSHIS_PER_BTC:
                        merchant.disable_all_credentials()
                        # TODO: poor UX, but let's wait until we actually have people doing this
                        msg = _('Your API credentials were unlinked from your CoinSafe account, please link your wallet again in order to sell bitcoin to customers.')
                        messages.success(request, msg)

                msg = _('Password succesfully updated.')
                messages.success(request, msg)

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))

    return {'form': form}
