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
    url = 'https://api.bitcoinaverage.com/ticker/global/USD/'
    r = requests.get(url)
    content = json.loads(r.content)
    fiat_btc = content['last']
    fiat_rate_formatted = "≈$%s" % '{:20,.2f}'.format(fiat_btc)
    json_response = json.dumps({"amount": fiat_rate_formatted})
    return HttpResponse(json_response, mimetype='application/json')