from bitcash.settings import BLOCKCYPHER_API_KEY

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

import requests
import json


def set_blockcypher_webhook(monitoring_address, callback_url, merchant=None):
    '''
    Set a blockcypher webhook to monitoring an address.

    We'll use this for the forwarding address, but the code here is generic
    and could be used for any address.

    http://dev.blockcypher.com/#webhooks

    '''

    assert is_valid_btc_address(monitoring_address), monitoring_address
    assert callback_url, 'Must supply a callback URL'

    payload = {
            # YUCK: this is how they do it though
            'filter': 'event=new-pool-tx&addr=%s' % monitoring_address,
            'url': callback_url,
            }

    if BLOCKCYPHER_API_KEY:
        payload['token'] = BLOCKCYPHER_API_KEY

    POST_URL = 'https://api.blockcypher.com/v1/btc/main/hooks'

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
