from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy

from annoying.decorators import render_to

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
    current_address = None
    transactions = None
    shopper = None
    forwarding_address = request.session.get('forwarding_address')
    if forwarding_address:
        current_address = ForwardingAddress.objects.get(b58_address=forwarding_address)
        transactions = current_address.get_all_transactions()
        shopper = current_address.get_current_shopper()
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
                    btc_address=current_address,
                )

                # Tie shopper to BTCTransaction model
                current_tx = current_address.get_transaction()
                if not current_tx.shopper:
                    current_tx.shopper = shopper
                    current_tx.save()

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
        return {
            'form': form,
            'user': user,
            'merchant': merchant,
            'shopper': shopper,
            'current_address': current_address,
            'transactions': transactions}

    return {
        'user': user,
        'merchant': merchant,
        'current_address': current_address,
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
