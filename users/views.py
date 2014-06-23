from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.contrib import messages

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from bitcoins.models import BTCTransaction, ForwardingAddress, ShopperBTCPurchase
from shoppers.models import Shopper
from shoppers.forms import ShopperInformationForm, BuyBitcoinForm, ConfirmPasswordForm


@render_to('index.html')
def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
    else:
        return {}


@login_required
@render_to('customer_dash/main.html')
def customer_dashboard(request):
    user = request.user
    if not user.get_merchant():
        return HttpResponseRedirect(reverse_lazy('register_merchant'))
    merchant = user.get_merchant()
    transactions, shopper = None, None
    forwarding_address_obj = get_object_or_None(ForwardingAddress,
            b58_address=request.session.get('forwarding_address'))
    buy_request = merchant.get_bitcoin_purchase_request()

    buy_form = BuyBitcoinForm(initial={'email_or_btc_address': '1'})
    password_form = ConfirmPasswordForm(user=user)
    shopper_form = ShopperInformationForm(initial={'phone_country': merchant.country})
    show_buy_modal = 'false'
    if request.method == 'POST':
        # if submitting a buy bitcoin form
        if 'amount' in request.POST:
            buy_form = BuyBitcoinForm(data=request.POST)
            if buy_form.is_valid():
                amount = buy_form.cleaned_data['amount']
                email_or_btc_address = buy_form.cleaned_data['email_or_btc_address']
                email = buy_form.cleaned_data['email']
                btc_address = buy_form.cleaned_data['btc_address']
                # Create shopper object
                btc_purchase = ShopperBTCPurchase.objects.create(
                    merchant=merchant,
                    email=email,
                    fiat_amount=amount,
                    b58_address=btc_address,
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
            if password_form.is_valid():
                if buy_request:
                    buy_request.pay_out_bitcoin()
                    msg = _('Success! Your bitcoin is now being sent. A receipt will be emailed to %s.' % buy_request.email)
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
    }


def simulate_deposit_detected(request):
    user = request.user
    merchant = user.get_merchant()
    btc_address = merchant.get_all_forwarding_addresses()[0]
    BTCTransaction.objects.create(
        satoshis=100000,
        forwarding_address=btc_address,
        merchant=merchant
    )
    return HttpResponseRedirect(reverse_lazy('deposit_dashboard'))
