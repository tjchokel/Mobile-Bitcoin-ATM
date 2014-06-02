from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy

from annoying.decorators import render_to

from bitcoins.models import BTCTransaction, ForwardingAddress
from shoppers.models import Shopper
from shoppers.forms import ShopperInformationForm


@login_required
@render_to('customer_dashboard.html')
def customer_dashboard(request):
    user = request.user
    merchant = user.get_merchant()
    current_address = '12345'  # FIXME: this should be passed in from previous page
    return {'user': user, 'merchant': merchant, 'current_address': current_address}


@login_required
@render_to('deposit_dashboard.html')
def deposit_dashboard(request):
    user = request.user
    merchant = user.get_merchant()
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

                return HttpResponseRedirect(reverse_lazy('deposit_dashboard'))
        return {
            'form': form,
            'user': user,
            'merchant': merchant,
            'shopper': shopper,
            'current_address': current_address,
            'transaction': transaction}
    else:
        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


def simulate_deposit_detected(request):
    user = request.user
    merchant = user.get_merchant()
    btc_address = merchant.get_all_forwarding_addresses()[0]
    BTCTransaction.objects.create(
        satoshis=12345678,
        forwarding_address=btc_address,
        merchant=merchant
    )
    return HttpResponseRedirect(reverse_lazy('deposit_dashboard'))
