from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from annoying.functions import get_object_or_None

from bitcoins.BCAddressField import is_valid_btc_address

from bitcoins.models import ForwardingAddress
from merchants.models import Merchant
from services.models import WebHook

from emails.trigger import send_admin_email

import json

from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy


@login_required
def poll_deposits(request):
    txns_grouped = []
    all_complete = False
    confs_needed = 6
    merchant = request.user.get_merchant()
    forwarding_obj = merchant.get_latest_forwarding_obj()
    if forwarding_obj:
        if forwarding_obj.activity_check_due():
            try:
                forwarding_obj.check_for_activity()
            except Exception as e:
                body_context = {
                        'merchant': request.user.get_merchant(),
                        'err_str': str(e),
                        }
                send_admin_email(
                        subject='BlockCypher API Call Failed %s' % now().isoformat()[:19],
                        body_template='poll_deposits_apicall.html',
                        body_context=body_context,
                        )
        # annoying:
        forwarding_obj = ForwardingAddress.objects.get(b58_address=forwarding_obj.b58_address)

        confs_needed = forwarding_obj.get_confs_needed()
        txns_grouped = forwarding_obj.get_and_group_all_transactions()
        if forwarding_obj.all_transactions_complete():
            all_complete = True

    json_dict = {
            'txns': txns_grouped,
            'all_complete': all_complete,
            'confs_needed': confs_needed,
            }
    json_response = json.dumps(json_dict, cls=DjangoJSONEncoder)
    return HttpResponse(json_response, content_type='application/json')


def get_bitcoin_price(request, merchant_id=None):
    if merchant_id:
        merchant = get_object_or_None(Merchant, id=merchant_id)
    else:
        user = request.user
        merchant = user.get_merchant()

    if merchant:
        merchant_btc_pricing_dict = merchant.get_merchant_btc_pricing_info()
    else:
        # should never happen
        merchant_btc_pricing_dict = {}

    json_response = json.dumps(merchant_btc_pricing_dict)
    return HttpResponse(json_response, content_type='application/json')


@csrf_exempt
def process_bci_webhook(request, random_id):
    # Log webhook
    WebHook.log_webhook(request, WebHook.BCI_PAYMENT_FORWARDED)

    # parse webhook
    input_txn_hash = request.GET['input_transaction_hash']
    destination_txn_hash = request.GET['transaction_hash']
    satoshis = int(request.GET['value'])
    num_confirmations = int(request.GET['confirmations'])
    input_address = request.GET['input_address']
    destination_address = request.GET['destination_address']

    # These defensive checks should always be true
    assert is_valid_btc_address(input_address), input_address
    assert is_valid_btc_address(destination_address), destination_address
    msg = '%s == %s' % (input_txn_hash, destination_txn_hash)
    assert input_txn_hash != destination_txn_hash, msg

    # process the transactions
    ForwardingAddress.handle_forwarding_txn(
            input_address=input_address,
            satoshis=satoshis,
            num_confirmations=num_confirmations,
            input_txn_hash=input_txn_hash,
            )
    ForwardingAddress.handle_destination_txn(
            forwarding_address=input_address,
            destination_address=destination_address,
            satoshis=satoshis,
            num_confirmations=num_confirmations,
            destination_txn_hash=destination_txn_hash,
            )

    if num_confirmations > 6:
        return HttpResponse("*ok*")
    else:
        return HttpResponse("Robot: please come back with more confirmations")


@login_required
def get_next_deposit_address(request):
    user = request.user
    merchant = user.get_merchant()
    forwarding_obj = merchant.get_or_set_available_forwarding_address()
    json_response = json.dumps({"address": forwarding_obj.b58_address})
    return HttpResponse(json_response, content_type='application/json')


@login_required
def customer_confirm_deposit(request):
    if request.method == 'POST':
        user = request.user
        merchant = user.get_merchant()
        forwarding_obj = merchant.get_latest_forwarding_obj()
        forwarding_obj.customer_confirmed_deposit_at = now()
        forwarding_obj.save()

    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


@login_required
def merchant_complete_deposit(request):
    if request.method == 'POST':
        user = request.user
        merchant = user.get_merchant()
        forwarding_obj = merchant.get_latest_forwarding_obj()

        if forwarding_obj.all_transactions_complete():
            forwarding_obj.paid_out_at = now()
            forwarding_obj.save()

            msg = _("Transaction complete. You can always see your transaction history by clicking the Admin button below.")
            messages.success(request, msg)

    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


@login_required
def cancel_address(request):
    if request.method == 'POST':
        user = request.user
        merchant = user.get_merchant()

        forwarding_obj = merchant.get_latest_forwarding_obj()

        forwarding_obj.cancelled_at = now()
        forwarding_obj.save()

        msg = _("Your request has been cancelled")
        messages.success(request, msg)

    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


@login_required
def cancel_buy(request):
    if request.method == 'POST':
        user = request.user
        merchant = user.get_merchant()

        buy_request = merchant.get_bitcoin_purchase_request()
        assert buy_request, 'No buy request to cancel'
        buy_request.mark_cancelled()

        msg = _("Your buy request has been cancelled")
        messages.success(request, msg)
    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
