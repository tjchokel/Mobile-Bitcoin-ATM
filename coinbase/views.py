from django.http import HttpResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from annoying.decorators import render_to
from django.utils.timezone import now

from coinbase.models import CBCredential
from coinbase.forms import CoinbaseAPIForm


@login_required
@render_to('merchants/coinbase.html')
def coinbase(request):
    user = request.user
    merchant = user.get_merchant()
    cb_credential = merchant.get_coinbase_credentials()

    form = CoinbaseAPIForm()
    if request.method == 'POST' and merchant:
        form = CoinbaseAPIForm(data=request.POST)
        if form.is_valid():
            # TODO: VALIDATE CREDENTIALS AND THEN UPDATE MODEL HERE

            api_key = form.cleaned_data['api_key']
            secret_key = form.cleaned_data['secret_key']
            credentials, created = CBCredential.objects.get_or_create(
                    merchant=merchant,
                    api_key=api_key,
                    api_secret=secret_key
            )
            try:
                balance = credentials.get_balance()
                messages.success(request, _('Your Coinbase API info has been updated'))
            except:
                credentials.disabled_at = now()
                credentials.save()
                messages.warning(request, _('Your Coinbase API credentials are not valid'))

            return HttpResponseRedirect(reverse_lazy('coinbase'))

    return {
        'user': user,
        'merchant': merchant,
        'form': form,
        'on_admin_page': True,
        'cb_credential': cb_credential,
    }


@login_required
def refresh_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    cb_credential = merchant.get_coinbase_credentials()
    try:
        balance = cb_credential.get_balance()
        messages.success(request, _('Your Coinbase API info has been refreshed'))
    except:
        messages.warning(request, _('Your Coinbase API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def disable_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    cb_credential = merchant.get_coinbase_credentials()
    cb_credential.disabled_at = now()
    cb_credential.save()
    return HttpResponse("*ok*")