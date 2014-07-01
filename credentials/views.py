from django.core.urlresolvers import reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.views.decorators.debug import sensitive_post_parameters
from annoying.decorators import render_to

from coinbase_wallets.models import CBSCredential
from blockchain_wallets.models import BCICredential
from bitstamp_wallets.models import BTSCredential

from credentials.forms import BlockchainAPIForm, CoinbaseAPIForm, BitstampAPIForm


@sensitive_post_parameters('username', 'main_password', 'second_password', )
@login_required
@render_to('merchants/blockchain.html')
def blockchain_creds(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_blockchain_credentials()

    form = BlockchainAPIForm()
    if request.method == 'POST' and merchant:
        form = BlockchainAPIForm(data=request.POST)
        if form.is_valid():
            credential, created = BCICredential.objects.get_or_create(
                    merchant=merchant,
                    username=form.cleaned_data['username'],
                    main_password=form.cleaned_data['main_password'],
                    second_password=form.cleaned_data['second_password'],
            )
            if created:
                credential.create_credential_link()

            try:
                credential.get_balance()
                messages.success(request, _('Your Blockchain API info has been updated'))
            except:
                credential.mark_disabled()
                messages.warning(request, _('Your Blockchain API credentials are not valid'))

            return HttpResponseRedirect(reverse_lazy('blockchain_creds'))

    return {
        'user': user,
        'merchant': merchant,
        'form': form,
        'on_admin_page': True,
        'credential': credential,
    }


@sensitive_post_parameters('api_key', 'secret_key')
@login_required
@render_to('merchants/coinbase.html')
def coinbase_creds(request):
    user = request.user
    merchant = user.get_merchant()
    cb_credential = merchant.get_coinbase_credentials()

    form = CoinbaseAPIForm()
    if request.method == 'POST' and merchant:
        form = CoinbaseAPIForm(data=request.POST)
        if form.is_valid():
            credential, created = CBSCredential.objects.get_or_create(
                    merchant=merchant,
                    api_key=form.cleaned_data['api_key'],
                    api_secret=form.cleaned_data['secret_key']
            )
            if created:
                credential.create_credential_link()

            try:
                credential.get_balance()
                messages.success(request, _('Your Coinbase API info has been updated'))
            except:
                credential.mark_disabled()
                messages.warning(request, _('Your Coinbase API credentials are not valid'))

            return HttpResponseRedirect(reverse_lazy('coinbase_creds'))

    return {
        'user': user,
        'merchant': merchant,
        'form': form,
        'on_admin_page': True,
        'cb_credential': cb_credential,
    }


@sensitive_post_parameters('username', 'api_key', 'secret_key')
@login_required
@render_to('merchants/bitstamp.html')
def bitstamp_creds(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credentials()

    form = BitstampAPIForm()
    if request.method == 'POST' and merchant:
        form = BitstampAPIForm(data=request.POST)
        if form.is_valid():
            credential, created = BTSCredential.objects.get_or_create(
                    merchant=merchant,
                    username=form.cleaned_data['username'],
                    api_key=form.cleaned_data['api_key'],
                    api_secret=form.cleaned_data['secret_key']
            )
            if created:
                credential.create_credential_link()

            try:
                credential.get_balance()
                messages.success(request, _('Your Bitstamp API info has been updated'))
            except:
                credential.mark_disabled()
                messages.warning(request, _('Your Bitstamp API credentials are not valid'))

            return HttpResponseRedirect(reverse_lazy('bitstamp_creds'))

    return {
        'user': user,
        'merchant': merchant,
        'form': form,
        'on_admin_page': True,
        'credential': credential,
    }


@login_required
def refresh_bci_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_blockchain_credentials()
    try:
        credential.get_balance()
        messages.success(request, _('Your Blockchain API info has been refreshed'))
    except:
        messages.warning(request, _('Your Blockchain API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def refresh_cb_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_coinbase_credentials()
    try:
        credential.get_balance()
        messages.success(request, _('Your Coinbase API info has been refreshed'))
    except:
        messages.warning(request, _('Your Coinbase API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def refresh_bs_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credentials()
    try:
        credential.get_balance()
        messages.success(request, _('Your Bistamp API info has been refreshed'))
    except:
        messages.warning(request, _('Your Bistamp API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def disable_bci_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_blockchain_credentials()
    credential.disabled_at = now()
    credential.save()
    return HttpResponse("*ok*")


@login_required
def disable_cb_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_coinbase_credentials()
    credential.disabled_at = now()
    credential.save()
    return HttpResponse("*ok*")


@login_required
def disable_bs_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credentials()
    credential.disabled_at = now()
    credential.save()
    return HttpResponse("*ok*")
