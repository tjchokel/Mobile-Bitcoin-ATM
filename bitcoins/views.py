from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from bitcoins.BCAddressField import is_valid_btc_address

from bitcoins.models import BTCTransaction, ForwardingAddress
from services.models import WebHook

import json
import requests


def poll_deposits(request):
    json_dict = {}
    json_dict['deposit'] = None
    json_dict['amount'] = None
    if request.session.get('forwarding_address'):
        address = ForwardingAddress.objects.get(b58_address=request.session.get('forwarding_address'))
        if address:
            txn = address.get_transaction()

            if txn:
                txn_dict = {'amount': txn.satoshis}
            else:
                txn_dict = None
            json_dict['deposit'] = txn_dict

    json_response = json.dumps(json_dict)
    return HttpResponse(json_response, mimetype='application/json')


@login_required
def get_bitcoin_price(request):
    user = request.user
    merchant = user.get_merchant()
    currency_code = merchant.currency_code or 'USD'
    url = 'https://api.bitcoinaverage.com/ticker/global/'+currency_code
    r = requests.get(url)
    content = json.loads(r.content)
    fiat_btc = content['last']
    basis_points_markup = merchant.basis_points_markup
    markup_fee = fiat_btc * basis_points_markup / 10000.00
    fiat_btc = fiat_btc - markup_fee
    fiat_rate_formatted = "%s%s" % (merchant.get_currency_symbol(), '{:20,.2f}'.format(fiat_btc))
    percent_markup = basis_points_markup / 100.00
    json_response = json.dumps({"amount": fiat_rate_formatted, "markup": percent_markup})
    return HttpResponse(json_response, mimetype='application/json')


def process_bci_webhook(request):
    input_txn_hash = request.GET['input_transaction_hash'][0]
    destination_txn_hash = request.GET['transaction_hash'][0]
    satoshis = int(request.GET['value'][0])
    num_confirmations = int(request.GET['confirmations'][0])
    input_address = request.GET['input_address']
    destination_address = request.GET['destination_address']

    assert is_valid_btc_address(input_address), input_address
    assert is_valid_btc_address(destination_address), destination_address

    msg = '%s == %s' % (input_txn_hash, destination_txn_hash)
    assert input_txn_hash != destination_txn_hash, msg

    # Log webhook like we do services API
    WebHook.create_webhook(request, WebHook.BCI_PAYMENT_FORWARDED)

    # Process the forwarding transaction
    BTCTransaction.process_forwarding_webhook(
            txn_hash=destination_txn_hash,
            satoshis=satoshis,
            conf_num=num_confirmations,
            forwarding_addr=None,
            destination_addr=destination_address)

    if num_confirmations >= 6:
        return HttpResponse("*ok*")
    else:
        msg = "Only %s confirmations, please try again when you have more"
        return HttpResponse(msg % num_confirmations)


@login_required
def get_next_deposit_address(request):
    user = request.user
    merchant = user.get_merchant()
    address = merchant.get_new_forwarding_address()
    request.session['forwarding_address'] = address
    json_response = json.dumps({"address": address})
    return HttpResponse(json_response, mimetype='application/json')
