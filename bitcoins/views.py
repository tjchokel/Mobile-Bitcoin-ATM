from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from annoying.functions import get_object_or_None
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import ugettext as _
from django.contrib import messages

from bitcoins.BCAddressField import is_valid_btc_address

from bitcoins.models import BTCTransaction, ForwardingAddress
from services.models import WebHook

from emails.internal_msg import send_admin_email
from utils import format_fiat_amount
import json


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
    currency_symbol = merchant.get_currency_symbol()
    fiat_btc = BTCTransaction.get_btc_market_price(currency_code)

    buy_markup_percent = merchant.get_cashin_percent_markup()
    sell_markup_percent = merchant.get_cashout_percent_markup()

    buy_markup_fee = fiat_btc * buy_markup_percent / 100.00
    sell_markup_fee = fiat_btc * sell_markup_percent / 100.00

    buy_price = fiat_btc + buy_markup_fee
    sell_price = fiat_btc - sell_markup_fee

    json_response = json.dumps({
                "no_markup_price": format_fiat_amount(fiat_btc, currency_symbol),
                "buy_price": format_fiat_amount(buy_price, currency_symbol),
                "sell_price": format_fiat_amount(sell_price, currency_symbol),
                "sell_price_no_format": round(sell_price, 2),
                "buy_price_no_format": round(buy_price, 2),
                # "markup": percent_markup,
                "buy_markup_percent": buy_markup_percent,
                "sell_markup_percent": sell_markup_percent,
                "currency_code": currency_code,
                "currency_symbol": currency_symbol,
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

    dest_btc_txn = get_object_or_None(BTCTransaction, txn_hash=destination_txn_hash)

    if dest_btc_txn:
        # already had txn in database

        # defensive check
        msg = '%s != %s' % (dest_btc_txn.satoshis, satoshis)
        assert dest_btc_txn.satoshis == satoshis, msg

        # update # confirms
        if num_confirmations < dest_btc_txn.conf_num:
            msg = 'BCI Reports %s confirms and previously reported %s confirms for txn %s'
            msg = msg % (num_confirmations, dest_btc_txn.conf_num, destination_txn_hash)
            raise Exception(msg)

        elif num_confirmations == dest_btc_txn.conf_num:
            # Same #, no need to update
            pass

        else:
            # Increase conf_num
            dest_btc_txn.conf_num = num_confirmations
            if num_confirmations >= 6 and not dest_btc_txn.irreversible_by:
                dest_btc_txn.irreversible_by = now()
            dest_btc_txn.save()
    else:
        # Didn't have TXN in DB

        # Lookup forwaring and destination address objects
        forwarding_obj = ForwardingAddress.objects.get(b58_address=input_address)
        destination_obj = forwarding_obj.destination_address

        msg = '%s != %s' % (destination_obj.b58_address, destination_address)
        assert destination_obj.b58_address == destination_address

        # Lookup fwd_btc_txn based on input_txn_hash
        fwd_btc_txn = get_object_or_None(BTCTransaction, txn_hash=input_txn_hash)

        # Run some safety checks and email us of discrepencies (but don't break)
        if fwd_btc_txn:
            if fwd_btc_txn.satoshis != satoshis:
                send_admin_email(
                        subject='BTC Discrepency for %s' % input_txn_hash,
                        message='Blockcypher says %s satoshis and BCI says %s' % (
                            fwd_btc_txn.satoshis, satoshis),
                        recipient_list=['monitoring@coinsafe.com', ],
                        )
            if fwd_btc_txn.conf_num < num_confirmations and num_confirmations <= 6:
                send_admin_email(
                        subject='Confirmations Discrepency for %s' % input_txn_hash,
                        message='Blockcypher says %s confs and BCI says %s' % (
                            fwd_btc_txn.conf_num, num_confirmations),
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
                input_btc_transaction=fwd_btc_txn,
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
            # skip this entry (it's the destination txn)
            continue

        fwd_btc_txn = get_object_or_None(BTCTransaction, txn_hash=txn_hash)

        if fwd_btc_txn:
            # already had txn in database

            # defensive check
            msg = '%s != %s' % (fwd_btc_txn.satoshis, output['value'])
            assert fwd_btc_txn.satoshis == output['value'], msg

            # update # confirms
            if confirmations < fwd_btc_txn.conf_num:
                msg = 'Blockcypher reports %s confirms and previously reported %s confirms for txn %s'
                msg = msg % (confirmations, fwd_btc_txn.conf_num, txn_hash)
                raise Exception(msg)

            elif confirmations == fwd_btc_txn.conf_num:
                # Same #, no need to update
                pass

            else:
                # Increase conf_num
                if confirmations >= 6 and not fwd_btc_txn.irreversible_by:
                    fwd_btc_txn.irreversible_by = now()
                fwd_btc_txn.conf_num = confirmations
                fwd_btc_txn.save()

                if fwd_btc_txn.meets_minimum_confirmations() and not fwd_btc_txn.met_minimum_confirmation_at:
                    # Mark it as such
                    fwd_btc_txn.met_minimum_confirmation_at = now()
                    fwd_btc_txn.save()

                    # send out emails
                    fwd_btc_txn.send_all_txconfirmed_notifications(force_resend=False)

        else:
            # Didn't have TXN in DB

            satoshis = output['value']
            fiat_amount = forwarding_obj.merchant.calculate_fiat_amount(satoshis=satoshis)

            # Confirmations logic
            if confirmations >= 6:
                # May want to make this variable and trigger email sending
                irreversible_by = now()
            else:
                irreversible_by = None

            # Create TX
            fwd_txn = BTCTransaction.objects.create(
                    txn_hash=txn_hash,
                    satoshis=satoshis,
                    conf_num=confirmations,
                    irreversible_by=irreversible_by,
                    forwarding_address=forwarding_obj,
                    currency_code_when_created=forwarding_obj.merchant.currency_code,
                    fiat_amount=fiat_amount,
                    )

            # Send out shopper/merchant emails
            if fwd_txn.meets_minimum_confirmations():
                # This shouldn't be the case, but it's a protection from things falling behind

                # Mark it as such
                fwd_btc_txn.met_minimum_confirmation_at = now()
                fwd_btc_txn.save()

                # Send confirmed notifications only (no need to send newtx notifications)
                fwd_txn.send_all_txconfirmed_notifications(force_resend=False)
            else:
                # It's new *and* not yet confirmed, this is what we expect
                fwd_txn.send_all_newtx_notifications(force_resend=False)

    return HttpResponse("*ok*")


@login_required
def get_next_deposit_address(request):
    user = request.user
    merchant = user.get_merchant()
    forwarding_address = request.session.get('forwarding_address')
    if forwarding_address:
        forwarding_obj = ForwardingAddress.objects.get(b58_address=forwarding_address)
        # if cookie forwarding address has not been used (user just closed modal)
        if forwarding_obj and forwarding_obj.can_be_reused():
            json_response = json.dumps({"address": forwarding_address})
            return HttpResponse(json_response, content_type='application/json')
    address = merchant.set_new_forwarding_address()
    request.session['forwarding_address'] = address
    json_response = json.dumps({"address": address})
    return HttpResponse(json_response, content_type='application/json')


@login_required
def customer_confirm_deposit(request):
    user = request.user
    merchant = user.get_merchant()

    forwarding_address = request.session.get('forwarding_address')
    assert forwarding_address, 'No forwarding address'
    address = ForwardingAddress.objects.get(b58_address=forwarding_address)

    msg = '%s != %s' % (merchant.id, address.merchant.id)
    assert merchant.id == address.merchant.id, msg

    address.customer_confirmed_deposit_at = now()
    address.save()

    return HttpResponse(json.dumps({}), content_type='application/json')


@login_required
def merchant_complete_deposit(request):
    user = request.user
    merchant = user.get_merchant()

    forwarding_address = request.session.get('forwarding_address')
    assert forwarding_address, 'No forwarding address'

    address = ForwardingAddress.objects.get(b58_address=forwarding_address)

    msg = '%s != %s' % (merchant.id, address.merchant.id)
    assert merchant.id == address.merchant.id, msg

    if address.all_transactions_complete():
        address.paid_out_at = now()
        address.save()
        del request.session['forwarding_address']

        msg = _("Transaction complete. You can always see your transaction history by clicking the Admin button below.")
        messages.success(request, msg)
    return HttpResponse(json.dumps({}), content_type='application/json')


@login_required
def cancel_address(request):
    user = request.user
    merchant = user.get_merchant()

    forwarding_address = request.session.get('forwarding_address')
    assert forwarding_address, 'No forwarding address'

    address = ForwardingAddress.objects.get(b58_address=forwarding_address)

    msg = '%s != %s' % (merchant.id, address.merchant.id)
    assert merchant.id == address.merchant.id, msg

    address.paid_out_at = now()
    address.save()
    del request.session['forwarding_address']

    msg = _("Your request has been cancelled")
    messages.success(request, msg)

    return HttpResponse(json.dumps({}), content_type='application/json')


@login_required
def cancel_buy(request):
    user = request.user
    merchant = user.get_merchant()

    buy_request = merchant.get_bitcoin_purchase_request()
    assert buy_request, 'No buy request to cancel'
    buy_request.cancelled_at = now()
    buy_request.save()

    msg = _("Your buy request has been cancelled")
    messages.success(request, msg)
    return HttpResponse(json.dumps({}), content_type='application/json')
