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
    return {}


@login_required
@render_to('customer_dash/customer_dashboard.html')
def customer_dashboard(request):
    user = request.user
    if not user.finished_registration():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    merchant = user.get_merchant()
    current_address = None
    transaction = None
    shopper = None
    if request.session.get('forwarding_address'):
        current_address = ForwardingAddress.objects.get(b58_address=request.session.get('forwarding_address'))
        transaction = current_address.get_transaction()
        shopper = current_address.get_current_shopper()
        form = ShopperInformationForm()
        if request.method == 'POST':
            form = ShopperInformationForm(data=request.POST)
            if form.is_valid():

                name = form.cleaned_data['name']
                email = form.cleaned_data['email']
                phone_num = form.cleaned_data['phone_num']

                shopper = Shopper.objects.create(
                    name=name,
                    email=email,
                    phone_num=phone_num,
                    btc_address=current_address,
                )

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
        return {
            'form': form,
            'user': user,
            'merchant': merchant,
            'shopper': shopper,
            'current_address': current_address,
            'transaction': transaction}

    return {
        'user': user,
        'merchant': merchant,
        'current_address': current_address,
        'transaction': transaction,
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
