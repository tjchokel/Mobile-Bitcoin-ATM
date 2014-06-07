from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from bitcoins.models import BTCTransaction, ForwardingAddress
from shoppers.models import Shopper
from shoppers.forms import ShopperInformationForm


@render_to('index.html')
def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
    else:
        return HttpResponseRedirect(reverse_lazy('login_request'))
    return {}


@login_required
@render_to('customer_dash/customer_dashboard.html')
def customer_dashboard(request):
    user = request.user
    if not user.finished_registration():
        return HttpResponseRedirect(reverse_lazy('register_merchant'))
    merchant = user.get_merchant()
    transactions, shopper = None, None
    forwarding_address_obj = get_object_or_None(ForwardingAddress,
            b58_address=request.session.get('forwarding_address'))
    if forwarding_address_obj:
        transactions = forwarding_address_obj.get_all_forwarding_transactions()
        form = ShopperInformationForm()
        if request.method == 'POST':
            form = ShopperInformationForm(data=request.POST)
            if form.is_valid():

                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                phone_num = form.cleaned_data['phone_num']

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

                return HttpResponseRedirect(reverse_lazy('merchant_profile'))
        return {
            'form': form,
            'user': user,
            'merchant': merchant,
            'shopper': shopper,
            'current_address': forwarding_address_obj,
            'transactions': transactions}

    return {
        'user': user,
        'merchant': merchant,
        'current_address': forwarding_address_obj,
        'transactions': transactions,
        'shopper': shopper,
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
