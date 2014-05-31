# coding: utf-8
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

import json
import requests


def poll_deposits(request):
    user = request.user
    business = user.get_business()
    address = business.get_current_address()
    txn = address.get_transaction()

    json_dict = {}
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
    business = user.get_business()
    currency_code = business.currency_code or 'USD'
    url = 'https://api.bitcoinaverage.com/ticker/global/'+currency_code
    r = requests.get(url)
    content = json.loads(r.content)
    fiat_btc = content['last']
    print fiat_btc
    basis_points_markup = business.basis_points_markup
    markup_fee = fiat_btc * basis_points_markup / 10000.00
    print markup_fee
    fiat_btc = fiat_btc - markup_fee
    print fiat_btc
    fiat_rate_formatted = "%s%s" % (business.get_currency_symbol(), '{:20,.2f}'.format(fiat_btc))
    percent_markup = basis_points_markup / 100.00
    json_response = json.dumps({"amount": fiat_rate_formatted, "markup": percent_markup})
    return HttpResponse(json_response, mimetype='application/json')


@login_required
def get_next_deposit_address(request):
    user = request.user
    business = user.get_business()
    address = business.get_next_address()
    json_response = json.dumps({"address": address.b58_address})
    return HttpResponse(json_response, mimetype='application/json')
