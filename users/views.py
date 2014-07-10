from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from bitcoins.models import BTCTransaction, ForwardingAddress, ShopperBTCPurchase
from shoppers.models import Shopper
from users.models import FutureShopper
from shoppers.forms import ShopperInformationForm, BuyBitcoinForm, NoEmailBuyBitcoinForm, ConfirmPasswordForm
from users.forms import CustomerRegistrationForm, ContactForm

from emails.trigger import send_and_log


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
    else:
        return {}


@sensitive_variables('password', 'password_form')
@sensitive_post_parameters('password', )
@login_required
@render_to('customer_dash/main.html')
def customer_dashboard(request):
    user = request.user
    merchant = user.get_merchant()
    if not merchant or not merchant.has_destination_address():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    transactions, shopper = None, None
    forwarding_address_obj = get_object_or_None(ForwardingAddress,
            b58_address=request.session.get('forwarding_address'))
    buy_request = merchant.get_bitcoin_purchase_request()

    if merchant.has_valid_coinbase_credentials():
        buy_form = BuyBitcoinForm(initial={'email_or_btc_address': '1'})
    else:
        buy_form = NoEmailBuyBitcoinForm()
    password_form = ConfirmPasswordForm(user=user)
    shopper_form = ShopperInformationForm(initial={'phone_country': merchant.country})
    show_buy_modal, show_confirm_purchase_modal = 'false', 'false'
    if request.method == 'POST':
        # if submitting a buy bitcoin form
        if 'amount' in request.POST:
            if merchant.has_valid_coinbase_credentials():
                buy_form = BuyBitcoinForm(data=request.POST)
            else:
                buy_form = NoEmailBuyBitcoinForm(data=request.POST)
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
            password_form = ConfirmPasswordForm(user=user, data=request.POST)
            show_confirm_purchase_modal = 'true'
            if password_form.is_valid():
                if buy_request:
                    buy_request.pay_out_bitcoin(send_receipt=True)
                    show_confirm_purchase_modal = 'false'
                    msg = _('Success! Your bitcoin is now being sent. A receipt will be emailed to %s.' % buy_request.shopper.email)
                    messages.success(request, msg, extra_tags='safe')
                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
    if forwarding_address_obj:
        # In case of refreshing the page later
        # Will be None on first use and be overwritten below
        shopper = forwarding_address_obj.shopper
        transactions = forwarding_address_obj.get_all_forwarding_transactions()

    return {
        'user': user,
        'merchant': merchant,
        'current_address': forwarding_address_obj,
        'transactions': transactions,
        'shopper': shopper,
        'buy_request': buy_request,
        'password_form': password_form,
        'shopper_form': shopper_form,
        'buy_form': buy_form,
        'show_buy_modal': show_buy_modal,
        'show_confirm_purchase_modal': show_confirm_purchase_modal,
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
                    message=form.cleaned_data['message'],
            )
            msg = _("Thanks! We'll email you when new businesses near you sign up.")
            messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('home'))

    return {'form': form}


@render_to('fixed_pages/contact.html')
def contact(request):
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
                subject='CoinSafe Support Form',
                body_template='admin/contact_form.html',
                to_merchant=None,
                to_email='support@coinsafe.com',
                to_name='CoinSafe Support',
                body_context=body_context,
                )
            msg = _("Thanks! We'll get back to you soon.")
            messages.success(request, msg, extra_tags='safe')
            return HttpResponseRedirect(reverse_lazy('contact'))

    return {'form': form}
