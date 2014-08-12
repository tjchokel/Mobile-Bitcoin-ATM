from bitcash.settings import BLOCKCYPHER_API_KEY

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

import requests
import json


def fetch_bcypher_txn_data_from_address(address, merchant=None, forwarding_obj=None):
    BASE_URL = 'http://api.blockcypher.com/v1/btc/main/addrs/%s'
    url_to_hit = BASE_URL % address

    if BLOCKCYPHER_API_KEY:
        url_to_hit += '?token=%s' % BLOCKCYPHER_API_KEY

    assert is_valid_btc_address(address), address

    r = requests.get(url_to_hit)

    # Log the API call
    APICall.objects.create(
            api_name=APICall.BLOCKCYPHER_TXN_FROM_ADDR,
            url_hit=url_to_hit,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=merchant,
            forwarding_address=forwarding_obj,
            )

    err_msg = 'Expected status code 2XX but got %s' % r.status_code
    assert str(r.status_code).startswith('2'), err_msg

    dict_response = json.loads(r.content)

    assert 'error' not in dict_response, dict_response
    assert 'errors' not in dict_response, dict_response

    return dict_response


def set_blockcypher_webhook(monitoring_address, callback_url, merchant=None):
    '''
    NOT USED ANYMORE

    Set a blockcypher webhook to monitoring an address.

    We'll use this for the forwarding address, but the code here is generic
    and could be used for any address.

    http://dev.blockcypher.com/#webhooks

    '''

    assert is_valid_btc_address(monitoring_address), monitoring_address
    assert callback_url, 'Must supply a callback URL'

    payload = {
            # YUCK: this is how they do it though
            'filter': 'event=tx-confirmation&addr=%s' % monitoring_address,
            'url': callback_url,
            }

    if BLOCKCYPHER_API_KEY:
        payload['token'] = BLOCKCYPHER_API_KEY

    POST_URL = 'http://api.blockcypher.com/v1/btc/main/hooks'

    r = requests.post(POST_URL, data=json.dumps(payload))

    # Log the API call
    APICall.objects.create(
            api_name=APICall.BLOCKCYPHER_ADDR_MONITORING,
            url_hit=POST_URL,
            response_code=r.status_code,
            post_params=payload,
            api_results=r.content,
            merchant=merchant)

    err_msg = 'Expected status code 201 but got %s' % r.status_code
    assert r.status_code == 201, err_msg

    dict_response = json.loads(r.content)

    err_msg = 'Expected 0 errors, got: %s' % dict_response['errors']
    assert dict_response['errors'] == 0, err_msg

    return dict_response
