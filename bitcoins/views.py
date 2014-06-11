from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from annoying.functions import get_object_or_None
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder

from bitcoins.BCAddressField import is_valid_btc_address

from bitcoins.models import BTCTransaction, ForwardingAddress
from services.models import WebHook

from emails.internal_msg import send_admin_email
from bitcash.settings import CAPITAL_CONTROL_COUNTRIES

import json
import requests


def poll_deposits(request):
    txns_grouped = []

    forwarding_address = request.session.get('forwarding_address')
    all_complete = False
    confs_needed = 6
    if forwarding_address:
        forwarding_obj = ForwardingAddress.objects.get(b58_address=forwarding_address)
        if forwarding_obj:
            confs_needed = forwarding_obj.get_confs_needed()
            txns_grouped = forwarding_obj.get_and_group_all_transactions()
            if forwarding_obj.all_transactions_complete():
                all_complete = True

    json_dict = {
            'deposits': {'txns': txns_grouped, 'all_complete': all_complete},
            'confs_needed': confs_needed,
            }
    json_response = json.dumps(json_dict, cls=DjangoJSONEncoder)
    return HttpResponse(json_response, content_type='application/json')


@login_required
def get_bitcoin_price(request):
    user = request.user
    merchant = user.get_merchant()
    currency_code = merchant.currency_code
    if currency_code in CAPITAL_CONTROL_COUNTRIES:
        url = 'https://conectabitcoin.com/en/market_prices.json'
        r = requests.get(url)
        content = json.loads(r.content)
        key = 'btc_'+currency_code.lower()
        fiat_btc = content[key]['sell']
    else:
        url = 'https://api.bitcoinaverage.com/ticker/global/'+currency_code
        r = requests.get(url)
        content = json.loads(r.content)
        fiat_btc = content['last']
    basis_points_markup = merchant.basis_points_markup
    markup_fee = fiat_btc * basis_points_markup / 10000.00
    fiat_btc = fiat_btc - markup_fee
    fiat_rate_formatted = "%s%s" % (merchant.get_currency_symbol(), '{:20,.2f}'.format(fiat_btc))
    percent_markup = basis_points_markup / 100.00
    json_response = json.dumps({
                "amount": fiat_rate_formatted,
                "markup": percent_markup,
                "currency_code": currency_code,
                })
    return HttpResponse(json_response, content_type='application/json')


@csrf_exempt
def process_bci_webhook(request, random_id):
    # Log webhook
    WebHook.log_webhook(request, WebHook.BCI_PAYMENT_FORWARDED)

    input_txn_hash = request.GET['input_transaction_hash']
    destination_txn_hash = request.GET['transaction_hash']
    satoshis = int(request.GET['value'])
    num_confirmations = int(request.GET['confirmations'])
    input_address = request.GET['input_address']
    destination_address = request.GET['destination_address']

    assert is_valid_btc_address(input_address), input_address
    assert is_valid_btc_address(destination_address), destination_address

    msg = '%s == %s' % (input_txn_hash, destination_txn_hash)
    assert input_txn_hash != destination_txn_hash, msg

    btc_txn = get_object_or_None(BTCTransaction, txn_hash=destination_txn_hash)

    if btc_txn:
        # already had txn in database

        # defensive check
        msg = '%s != %s' % (btc_txn.satoshis, satoshis)
        assert btc_txn.satoshis == satoshis, msg

        # update # confirms
        if num_confirmations < btc_txn.conf_num:
            msg = 'BCI Reports %s confirms and previously reported %s confirms for txn %s'
            msg = msg % (num_confirmations, btc_txn.conf_num, destination_txn_hash)
            raise Exception(msg)

        elif num_confirmations == btc_txn.conf_num:
            # Same #, no need to update
            pass

        else:
            # Increase conf_num
            btc_txn.conf_num = num_confirmations
            if num_confirmations >= 6 and not btc_txn.irreversible_by:
                btc_txn.irreversible_by = now()
            btc_txn.save()
    else:
        # Didn't have TXN in DB

        # Lookup forwaring and destination address objects
        forwarding_obj = ForwardingAddress.objects.get(b58_address=input_address)
        destination_obj = forwarding_obj.destination_address

        msg = '%s != %s' % (destination_obj.b58_address, destination_address)
        assert destination_obj.b58_address == destination_address

        # Lookup input_btc_transaction based on input_txn_hash
        input_btc_transaction = get_object_or_None(BTCTransaction, txn_hash=input_txn_hash)

        # Run some safety checks and email us of discrepencies (but don't break)
        if input_btc_transaction:
            if input_btc_transaction.satoshis != satoshis:
                send_admin_email(
                        subject='BTC Discrepency for %s' % input_txn_hash,
                        message='Blockcypher says %s satoshis and BCI says %s' % (
                            input_btc_transaction.satoshis, satoshis),
                        recipient_list=['monitoring@coinsafe.com', ],
                        )
            if input_btc_transaction.conf_num < num_confirmations and num_confirmations <= 6:
                send_admin_email(
                        subject='Confirmations Discrepency for %s' % input_txn_hash,
                        message='Blockcypher says %s confs and BCI says %s' % (
                            input_btc_transaction.conf_num, num_confirmations),
                        recipient_list=['monitoring@coinsafe.com', ],
                        )

        # Confirmations logic
        if num_confirmations >= 6:
            # May want to make this a failover in case blockcypher is down
            irreversible_by = now()
        else:
            irreversible_by = None

        # Create TX
        BTCTransaction.objects.create(
                txn_hash=destination_txn_hash,
                satoshis=satoshis,
                conf_num=num_confirmations,
                irreversible_by=irreversible_by,
                forwarding_address=forwarding_obj,
                destination_address=destination_obj,
                input_btc_transaction=input_btc_transaction,
                )

    if num_confirmations >= 6:
        return HttpResponse("*ok*")
    else:
        msg = "Only %s confirmations, please try again when you have more"
        return HttpResponse(msg % num_confirmations)


def get_forwarding_obj_from_address_list(address_list):
    ' Helper function that returns the first matching fowrwarding obj, or none'

    for address in address_list:
        forwarding_obj = get_object_or_None(ForwardingAddress, b58_address=address)
        if forwarding_obj:
            return forwarding_obj

    return None


@csrf_exempt
def process_blockcypher_webhook(request, random_id):
    # Log webhook
    WebHook.log_webhook(request, WebHook.BLOCKCYPHER_ADDR_MONITORING)

    assert request.method == 'POST', 'Request has no post'

    payload = json.loads(request.body)

    confirmations = payload['confirmations']
    txn_hash = payload['hash']

    for output in payload['outputs']:
        # Make sure it has an address we care about:
        forwarding_obj = get_forwarding_obj_from_address_list(output['addresses'])
        if not forwarding_obj:
            # skip this entry
            continue

        btc_txn = get_object_or_None(BTCTransaction, txn_hash=txn_hash)

        if btc_txn:
            # already had txn in database

            # defensive check
            msg = '%s != %s' % (btc_txn.satoshis, output['value'])
            assert btc_txn.satoshis == output['value'], msg

            # update # confirms
            if confirmations < btc_txn.conf_num:
                msg = 'Blockcypher reports %s confirms and previously reported %s confirms for txn %s'
                msg = msg % (confirmations, btc_txn.conf_num, txn_hash)
                raise Exception(msg)

            elif confirmations == btc_txn.conf_num:
                # Same #, no need to update
                pass

            else:
                # Increase conf_num
                btc_txn.conf_num = confirmations
                if confirmations >= 6 and not btc_txn.irreversible_by:
                    btc_txn.irreversible_by = now()
                btc_txn.save()
        else:
            # Didn't have TXN in DB

            # Confirmations logic
            if confirmations >= 6:
                # May want to make this variable and trigger email sending
                irreversible_by = now()
            else:
                irreversible_by = None

            # Create TX
            BTCTransaction.objects.create(
                    txn_hash=txn_hash,
                    satoshis=output['value'],
                    conf_num=confirmations,
                    irreversible_by=irreversible_by,
                    forwarding_address=forwarding_obj,
                    )

    return HttpResponse("*ok*")


@login_required
def get_next_deposit_address(request):
    user = request.user
    merchant = user.get_merchant()
    address = merchant.get_new_forwarding_address()
    request.session['forwarding_address'] = address
    json_response = json.dumps({"address": address})
    return HttpResponse(json_response, content_type='application/json')


@login_required
def confirm_deposit(request):
    user = request.user
    merchant = user.get_merchant()
    if request.session.get('forwarding_address'):
        address = ForwardingAddress.objects.get(b58_address=request.session.get('forwarding_address'))
        if address and merchant.id == address.merchant.id:
            address.user_confirmed_deposit_at = now()
            address.save()

    return HttpResponse(json.dumps({}), content_type='application/json')


@login_required
def complete_deposit(request):
    user = request.user
    merchant = user.get_merchant()
    if request.session.get('forwarding_address'):
        address = ForwardingAddress.objects.get(b58_address=request.session.get('forwarding_address'))
        if address and merchant.id == address.merchant.id:
            if address.all_transactions_complete():
                address.paid_out_at = now()
                address.save()
                request.session['forwarding_address'] = None

    return HttpResponse(json.dumps({}), content_type='application/json')


@login_required
def cancel_address(request):
    user = request.user
    merchant = user.get_merchant()
    if request.session.get('forwarding_address'):
        address = ForwardingAddress.objects.get(b58_address=request.session.get('forwarding_address'))
        if address and merchant.id == address.merchant.id:
            address.paid_out_at = now()
            address.save()
            request.session['forwarding_address'] = None

    return HttpResponse(json.dumps({}), content_type='application/json')
