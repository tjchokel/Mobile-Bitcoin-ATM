from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.views.decorators.debug import sensitive_post_parameters
from django.shortcuts import get_object_or_404

from annoying.decorators import render_to

from credentials.models import BaseCredential
from coinbase_wallets.models import CBSCredential
from blockchain_wallets.models import BCICredential
from bitstamp_wallets.models import BTSCredential

from credentials.forms import BitcoinCredentialsForm, SENSITIVE_CRED_PARAMS

import json


def refresh_credentials(request):
    pass


@sensitive_post_parameters(*SENSITIVE_CRED_PARAMS)
@login_required
@render_to('merchants/wallet.html')
def base_creds(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_valid_api_credential()
    if False:
        if credential:
            credential.disabled_at = now()
            credential.save()
            messages.success(request, _('Your API Credentials Have Been Removed from Your Account'))
        else:
            messages.warning(request, _('No API Credential Found'))

    add_cred_form = BitcoinCredentialsForm(initial={'exchange_choice': 'coinbase'})
    if request.method == 'POST':
        if 'exchange_choice' in request.POST:
            add_cred_form = BitcoinCredentialsForm(data=request.POST)
            INVALID_MSG = _('Your API credentials are not valid. Please try again.')
            if add_cred_form.is_valid():
                exchange_choice = add_cred_form.cleaned_data['exchange_choice']

                credential = None

                if exchange_choice == 'coinbase':
                    credential, created = CBSCredential.objects.get_or_create(
                            merchant=merchant,
                            api_key=add_cred_form.cleaned_data['cb_api_key'],
                            api_secret=add_cred_form.cleaned_data['cb_secret_key'],
                            )
                if exchange_choice == 'blockchain':
                    credential, created = BCICredential.objects.get_or_create(
                            merchant=merchant,
                            username=add_cred_form.cleaned_data['bci_username'],
                            main_password=add_cred_form.cleaned_data['bci_main_password'],
                            second_password=add_cred_form.cleaned_data['bci_second_password'],
                            )
                if exchange_choice == 'bitstamp':
                    credential, created = BTSCredential.objects.get_or_create(
                            merchant=merchant,
                            customer_id=add_cred_form.cleaned_data['bs_customer_id'],
                            api_key=add_cred_form.cleaned_data['bs_api_key'],
                            api_secret=add_cred_form.cleaned_data['bs_secret_key'],
                            )
                if not created:
                    credential.deleted_at = None
                    credential.last_succeded_at = None
                    credential.last_failed_at = None
                    credential.save()

                try:
                    balance = credential.get_balance()
                    if balance is False:
                        messages.warning(request, INVALID_MSG)
                        # This error will be caught by the try/except and not logged:
                        raise Exception('Could Not Fetch Balance')
                    # Get new address if API partner permits, otherwise get an existing one
                    credential.get_best_receiving_address(set_as_merchant_address=True)
                    credential.mark_success()
                    # FIXME: mark all other credentials as invalid
                    SUCCESS_MSG = _('Your API credentials were succesfully added. Any bitcoin you buy will be sent to your %(credential_name)s account.' % {
                        'credential_name': credential.get_credential_to_display()}
                        )
                    messages.success(request, SUCCESS_MSG)
                except:
                    credential.mark_disabled()
                    messages.warning(request, INVALID_MSG)

        elif 'delete_credentials' in request.POST:
            pass

    return {
            'credential': credential,
            'add_cred_form': add_cred_form,
            'merchant': merchant,
            'dest_obj': merchant.get_destination_address,
            }


@login_required
def refresh_bci_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_blockchain_credential()
    success = False

    try:
        balance = credential.get_balance()
        if balance is not False:
            success = True
    except:
        pass

    if success:
        messages.success(request, _('Your Blockchain API info has been refreshed'))
    else:
        messages.warning(request, _('Your Blockchain API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def refresh_cb_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_coinbase_credential()
    success = False

    try:
        balance = credential.get_balance()
        if balance is not False:
            success = True
    except:
        pass

    if success:
        messages.success(request, _('Your Coinbase API info has been refreshed'))
    else:
        messages.warning(request, _('Your Coinbase API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def refresh_bs_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credential()
    success = False
    try:
        balance = credential.get_balance()
        if balance is not False:
            success = True
    except:
        pass

    if success:
        messages.success(request, _('Your Bistamp API info has been refreshed'))
    else:
        messages.warning(request, _('Your Bistamp API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def get_new_address(request, credential_id):
    credential = get_object_or_404(BaseCredential, id=credential_id)

    user = request.user
    merchant = user.get_merchant()
    assert credential.merchant == merchant, 'potential hacker alert!'

    dict_response = {'new_address': credential.get_best_receiving_address()}

    return HttpResponse(json.dumps(dict_response), content_type='application/json')


@login_required
def get_credential_balance(request, credential_id):
    credential = get_object_or_404(BaseCredential, id=credential_id)

    user = request.user
    merchant = user.get_merchant()

    assert credential.merchant == merchant, 'potential hacker alert!'

    dict_response = {'balance': credential.get_balance()}

    return HttpResponse(json.dumps(dict_response), content_type='application/json')
