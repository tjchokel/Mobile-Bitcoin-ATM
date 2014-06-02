from bitcash.settings import BCI_SECRET_KEY

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

import requests
import json

from urllib import urlencode


def set_bci_webhook(dest_address, callback_url, merchant=None):
    '''
    Set a blockchain.info webhook to generate a recieving address that will forward to dest_address

    Note: the minimum supported transaction size is 0.001 BTC
    https://blockchain.info/api/api_receive
    '''

    # TODO: secure callback with some sort of an API key as a URL param

    cb_section = urlencode({'callback': callback_url})
    bci_url = 'https://blockchain.info/api/receive?method=create&address=%s&%s' % (
            dest_address, cb_section)
    r = requests.get(bci_url)

    # Log the API call
    APICall.objects.create(
            api_name=APICall.BCI_RECIEVE_PAYMENTS,
            url_hit=bci_url,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=merchant)

    err_msg = 'Expected status code 200 but got %s' % r.status_code
    assert r.status_code == 200, err_msg

    resp_json = json.loads(r.content)

    # Safety checks
    assert resp_json['fee_percent'] == 0
    assert resp_json['destination'] == dest_address
    assert resp_json['callback_url'] == callback_url

    assert is_valid_btc_address(resp_json['input_address'])

    return resp_json['input_address']

# UNUSED METHODS:


def fetch_bci_txn_data_from_hash(txn_hash, merchant=None):
    url = 'https://blockchain.info/rawtx/%s?api_code=%s' % (txn_hash,
            BCI_SECRET_KEY)
    r = requests.get(url)

    # Log the API call
    APICall.objects.create(
            api_name=APICall.BCI_TXN_FROM_HASH,
            url_hit=url,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=merchant)

    err_msg = 'Expected status code 200 but got %s' % r.status_code
    assert r.status_code == 200, err_msg

    return json.loads(r.content)


def fetch_bci_txn_data(address, merchant=None):
    """
    Get all BCI transactions for a given address
    """
    assert address, 'Must supply an address'
    bci_url = 'https://blockchain.info/address/%s?format=json&api_code=%s' % (
            address, BCI_SECRET_KEY)
    r = requests.get(bci_url)

    # Log the API call
    APICall.objects.create(
            api_name=APICall.BCI_TXN_FROM_ADDR,
            url_hit=bci_url,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=merchant)

    err_msg = 'Expected status code 200 but got %s' % r.status_code
    assert r.status_code == 200, err_msg
    return json.loads(r.content)
