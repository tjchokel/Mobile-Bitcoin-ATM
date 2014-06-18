import hashlib
import hmac
import time
import requests


def get_cb_request(url, api_key, api_secret, body=None):
    """
    Modified from example here:
    https://coinbase.com/docs/api/authentication
    https://coinbase.com/docs/api/ecommerce_tutorial

    CB API is non-standard and undocumented.
    For kwargs, use a get string as the `url` and no body. Easy.
    For POSTing a JSON object, encode them as a query_string (in the
    following nonstandard way) and post it as such:

    {'transation': {'to': 'foo', 'amount': 1}}
    ->
    transaction[to]=foo&transaction[amount]=1
    """
    # convert from unicode to str
    api_key = str(api_key)
    api_secret = str(api_secret)

    #print 'incoming body', body
    #print 'url:', url

    nonce = int(time.time() * 1e6)
    #print 'nonce:', nonce
    message = str(nonce) + url
    if body:
        message += body
    #print 'message (after editing):', message
    signature = hmac.new(api_secret, message, hashlib.sha256).hexdigest()
    #print 'signature:', signature
    headers = {
            #"Content-Type": 'application/x-www-form-urlencoded',
            'ACCESS_KEY': api_key,
            'ACCESS_SIGNATURE': signature,
            'ACCESS_NONCE': nonce,
            }
    if body:
        return requests.post(url, data=body, headers=headers)
    return requests.get(url, headers=headers)
