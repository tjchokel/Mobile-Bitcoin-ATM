from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

from bitcash.settings import CHAIN_COM_API_KEY

import requests
import json


def fetch_chaincom_txn_data_from_address(address, merchant=None, forwarding_obj=None):
    BASE_URL = 'https://api.chain.com/v1/bitcoin/addresses/%s/transactions'
    url_to_hit = BASE_URL % address

    if CHAIN_COM_API_KEY:
        url_to_hit += '?api-key-id=%s' % CHAIN_COM_API_KEY

    assert is_valid_btc_address(address), address

    r = requests.get(url_to_hit)

    # Log the API call
    APICall.objects.create(
            api_name=APICall.CHAINCOM_TXN_FROM_ADDR,
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


def filter_chaincom_txns(forwarding_address, destination_address, txn_data):
    '''
    Take the results from fetch_chaincom_txn_data_from_address and filter out
    only ones with addresses we care about (outputs to the forwarding or destination address).

    Return a list of the following form:
    (
        (address, satoshis, confirmations, txn_hash, )
    )
    '''
    txn_data_filtered = []
    for txn in txn_data:

        # outputs only
        for txn_output in txn['outputs']:
            for output_address in txn_output['addresses']:
                if output_address == forwarding_address:
                    txn_data_filtered.append((
                        output_address,
                        txn_output['value'],
                        txn['confirmations'],
                        txn['hash'],
                        ))
                elif output_address == destination_address:
                    # only count this if it was sent from the forwarding address
                    for txn_input in txn['inputs']:
                        for input_address in txn_input['addresses']:
                            if input_address == forwarding_address:
                                txn_data_filtered.append((
                                    output_address,
                                    txn_output['value'],
                                    txn['confirmations'],
                                    txn['hash'],
                                    ))

    return txn_data_filtered
