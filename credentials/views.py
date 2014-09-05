from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.views.decorators.debug import sensitive_post_parameters
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse_lazy

from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from credentials.models import BaseCredential, BaseAddressFromCredential
from coinbase_wallets.models import CBSCredential
from blockchain_wallets.models import BCICredential
from bitstamp_wallets.models import BTSCredential

from credentials.forms import BitcoinCredentialsForm, DeleteCredentialForm, SENSITIVE_CRED_PARAMS

from utils import format_satoshis_with_units, format_satoshis_with_units_rounded

import json

from datetime import timedelta


@sensitive_post_parameters(*SENSITIVE_CRED_PARAMS)
@login_required
@render_to('merchants/wallet.html')
def base_creds(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_api_credential()

    add_cred_form = BitcoinCredentialsForm(initial={'exchange_choice': 'coinbase'})
    del_cred_form = None
    if credential:
        del_cred_form = DeleteCredentialForm(initial={'credential_id': credential.id})

    if request.method == 'POST':
        if 'exchange_choice' in request.POST:
            add_cred_form = BitcoinCredentialsForm(data=request.POST)
            INVALID_MSG = _('Your API credentials are not valid. Please try again.')
            if add_cred_form.is_valid():
                exchange_choice = add_cred_form.cleaned_data['exchange_choice']

                credential = None

                if exchange_choice == 'coinbase':
                    credential = CBSCredential.objects.create(
                            merchant=merchant,
                            api_key=add_cred_form.cleaned_data['cb_api_key'],
                            api_secret=add_cred_form.cleaned_data['cb_secret_key'],
                            )
                elif exchange_choice == 'blockchain':
                    credential = BCICredential.objects.create(
                            merchant=merchant,
                            username=add_cred_form.cleaned_data['bci_username'],
                            main_password=add_cred_form.cleaned_data['bci_main_password'],
                            second_password=add_cred_form.cleaned_data['bci_second_password'],
                            )
                elif exchange_choice == 'bitstamp':
                    credential = BTSCredential.objects.create(
                            merchant=merchant,
                            customer_id=add_cred_form.cleaned_data['bs_customer_id'],
                            api_key=add_cred_form.cleaned_data['bs_api_key'],
                            api_secret=add_cred_form.cleaned_data['bs_secret_key'],
                            )
                else:
                    raise Exception('Logic Fail. Unknown Exchange Choice')

                try:
                    # Get new address if API partner permits, otherwise get an existing one
                    credential.get_best_receiving_address(set_as_merchant_address=True)
                    satoshis = credential.get_balance()
                    if satoshis is False:
                        raise Exception('No Balance Permissions: used to toggle this as a failure below')

                    SUCCESS_MSG = _('Your %(credential_name)s API credentials were succesfully added. Any bitcoin you buy will be sent to this account.' % {
                        'credential_name': credential.get_credential_to_display()}
                        )
                    messages.success(request, SUCCESS_MSG)

                    # Redirect on success to handle edge cases
                    return HttpResponseRedirect(reverse_lazy('base_creds'))

                except:
                    credential.mark_disabled()
                    credential = None
                    messages.warning(request, INVALID_MSG)

        elif 'credential_id' in request.POST:
            del_cred_form = DeleteCredentialForm(data=request.POST)
            if del_cred_form.is_valid():
                credential = get_object_or_None(BaseCredential, id=del_cred_form.cleaned_data['credential_id'])
                # Fail loudly, this shouldn't be possible
                assert credential, 'Hacker or Bug Alert: credential missing'

                assert credential.merchant == merchant, 'Hacker or Bug Alert: credential not beloning to merchant'

                # Disable any lingering credentials (to be cautious)
                merchant.disable_all_credentials()

                DEL_MSG = _('Your %(credential_name)s API credentials were removed. Please add new credentials in order to use CoinSafe.' % {
                    'credential_name': credential.get_credential_to_display()})

                credential = None
                messages.info(request, DEL_MSG)

                # Redirect on success to handle edge cases
                return HttpResponseRedirect(reverse_lazy('base_creds'))

            else:
                raise Exception('Invalid Delete Credential: should not be possible')

        else:
            raise Exception('Logic Fail: users post not understood')

    return {
            'credential': credential,
            'add_cred_form': add_cred_form,
            'del_cred_form': del_cred_form,
            'merchant': merchant,
            'dest_obj': merchant.get_destination_address,
            }


@login_required
def get_new_address(request, credential_id):
    credential = get_object_or_404(BaseCredential, id=credential_id)

    user = request.user
    merchant = user.get_merchant()
    assert credential.merchant == merchant, 'potential hacker alert!'

    recent_time = now() - timedelta(minutes=10)
    base_address_objs = BaseAddressFromCredential.objects.filter(
            credential=credential, created_at__gt=recent_time).order_by('-created_at')
    if base_address_objs:
        # Don't make API call for a new address unless it has been a while
        best_address = base_address_objs[0].b58_address
    else:
        best_address = credential.get_best_receiving_address()

    dict_response = {'new_address': best_address}

    return HttpResponse(json.dumps(dict_response), content_type='application/json')


@login_required
def get_current_balance(request, credential_id):
    credential = get_object_or_404(BaseCredential, id=credential_id)

    user = request.user
    merchant = user.get_merchant()

    assert credential.merchant == merchant, 'potential hacker alert!'

    satoshis = credential.get_balance()

    if satoshis is False:
        pass

    dict_response = {
            'satoshis': satoshis,
            'fswu': format_satoshis_with_units(satoshis),
            'fswur': format_satoshis_with_units_rounded(satoshis),
            }

    return HttpResponse(json.dumps(dict_response), content_type='application/json')


@login_required
def refresh_credentials(request, credential_id):
    credential = get_object_or_404(BaseCredential, id=credential_id)

    user = request.user
    merchant = user.get_merchant()
    success = False

    assert credential.merchant == merchant, 'potential hacker alert!'

    try:
        balance = credential.get_balance()
        if balance is not False:
            success = True
    except:
        pass

    if success:
        messages.success(request, _('Your API credentials are valid'))
    else:
        messages.warning(request, _('Your API credentials appear to be invalid'))
    return HttpResponse("*ok*")
