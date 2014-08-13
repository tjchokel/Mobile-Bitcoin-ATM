from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from bitcoins.BCAddressField import is_valid_btc_address

from bitcoins.models import BTCTransaction, ForwardingAddress
from services.models import WebHook

from utils import format_fiat_amount
import json


from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy


def poll_deposits(request):
    txns_grouped = []
    all_complete = False
    confs_needed = 6
    forwarding_address = request.session.get('forwarding_address')
    if forwarding_address:
        forwarding_obj = ForwardingAddress.objects.get(b58_address=forwarding_address)
        if forwarding_obj:
            if forwarding_obj.activity_check_due():
                forwarding_obj.check_for_activity()
            # annoying:
            forwarding_obj = ForwardingAddress.objects.get(b58_address=forwarding_obj.b58_address)
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
    if request.method == 'POST':
        user = request.user
        merchant = user.get_merchant()

        forwarding_address = request.session.get('forwarding_address')
        assert forwarding_address, 'No forwarding address'
        address = ForwardingAddress.objects.get(b58_address=forwarding_address)

        msg = '%s != %s' % (merchant.id, address.merchant.id)
        assert merchant.id == address.merchant.id, msg

        address.customer_confirmed_deposit_at = now()
        address.save()

    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


@login_required
def merchant_complete_deposit(request):
    if request.method == 'POST':
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

    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))


@login_required
def cancel_address(request):
    if request.method == 'POST':
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
