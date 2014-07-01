from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now

from credentials.models import (BaseCredential, BaseBalance, BaseSentBTC,
        BaseSellBTC, CredentialLink)
from services.models import APICall
from bitcoins.models import BTCTransaction

from bitcoins.BCAddressField import is_valid_btc_address

from utils import btc_to_satoshis, satoshis_to_btc

import json
import hashlib
import hmac
import time
import requests


CB_DEBUG = False


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

    nonce = int(time.time() * 1e6)
    message = str(nonce) + url
    if body:
        message += body
    signature = hmac.new(api_secret, message, hashlib.sha256).hexdigest()
    headers = {
            'ACCESS_KEY': api_key,
            'ACCESS_SIGNATURE': signature,
            'ACCESS_NONCE': nonce,
            }

    if CB_DEBUG:
        print '-'*75
        print 'url:', url
        print 'body:', body
        print 'nonce:', nonce
        print 'message:', message
        print 'signature:', signature
        print '-'*75

    if body:
        return requests.post(url, data=body, headers=headers, verify=True)
    return requests.get(url, headers=headers, verify=True)


class CBSCredential(BaseCredential):

    api_key = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=256, blank=False, null=False, db_index=True)

    def save(self, *args, **kwargs):
        """ Create the CredentialLink object on the first save """
        if not self.pk:
            # This only happens if the objects isn't in the database yet.
            # http://stackoverflow.com/a/2311499/1754586
            CredentialLink.objects.create(cbs_credential=self)
        super(CBSCredential, self).save(*args, **kwargs)

    def get_balance(self):
        """
        Return acount balance in satoshis
        """
        BALANCE_URL = 'https://coinbase.com/api/v1/account/balance'
        r = get_cb_request(
                url=BALANCE_URL,
                api_key=self.api_key,
                api_secret=self.api_secret)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_BALANCE,
            url_hit=BALANCE_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        currency_returned = resp_json['currency']
        assert currency_returned == 'BTC', currency_returned

        satoshis = btc_to_satoshis(resp_json['amount'])

        # Record the balance results
        BaseBalance.objects.create(satoshis=satoshis,
                credential_link=self.credentiallink)

        return satoshis

    def list_recent_purchases_and_sales(self):
        # TODO: add DB logging?
        LIST_FIAT_URL = 'https://coinbase.com/api/v1/transfers'

        url_to_hit = LIST_FIAT_URL+'?limit=100'

        r = get_cb_request(
                url=url_to_hit,
                api_key=self.api_key,
                api_secret=self.api_secret,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_LIST_PURCHASE_SALE,
            url_hit=url_to_hit,
            response_code=r.status_code,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        return json.loads(r.content)['transfers']

    def list_recent_btc_transactions(self):
        ''' Limits to 30, add pagination if you want more '''
        LIST_TX_URL = 'https://coinbase.com/api/v1/transactions'

        r = get_cb_request(
                url=LIST_TX_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_LIST_BTC_TRANSACTIONS,
            url_hit=LIST_TX_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        json_resp = json.loads(r.content)

        # Record the balance
        BaseBalance.objects.create(
                satoshis=btc_to_satoshis(json_resp['balance']['amount']),
                credential_link=self.credentiallink
                )

        # Return transactions
        return json_resp['transactions']

    def request_cashout(self, satoshis_to_sell):
        SELL_URL = 'https://coinbase.com/api/v1/sells'

        btc_to_sell = satoshis_to_btc(satoshis_to_sell)
        body_to_use = 'qty=%s' % btc_to_sell

        r = get_cb_request(
                url=SELL_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                body=body_to_use,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_CASHOUT_BTC,
            url_hit=SELL_URL,
            response_code=r.status_code,
            api_results=r.content,
            post_params=body_to_use,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        success = resp_json['success']
        assert success is True, '%s: %s' % (success, resp_json.get('errors'))

        transfer = resp_json['transfer']

        status = transfer['status']
        assert status.lower() in ('pending', 'created'), status

        btc_obj = transfer['btc']
        assert btc_obj['currency'] == 'BTC', btc_obj

        satoshis = btc_to_satoshis(btc_obj['amount'])
        assert satoshis == satoshis_to_sell, btc_obj['amount']

        currency_to_recieve = transfer['total']['currency']

        fiat_fees_in_cents = 0
        for fee_key in transfer['fees']:
            fee = transfer['fees'][fee_key]
            fiat_fees_in_cents += int(fee['cents'])
            msg = '%s != %s' % (fee['currency_iso'], currency_to_recieve)
            assert fee['currency_iso'] == currency_to_recieve, msg
        fiat_fees = fiat_fees_in_cents/100.0

        cbs_sell_btc = CBSSellBTC.objects.create(coinbase_code=transfer['code'])

        return CBSSellBTC.objects.create(
                credential_link=self.credentiallink,
                cbs_sell_btc=cbs_sell_btc,
                satoshis=satoshis,
                currency_code=currency_to_recieve,
                fees_in_fiat=fiat_fees,
                to_receive_in_fiat=float(transfer['total']['amount']),
                )

    def send_btc(self, satoshis_to_send, destination_btc_address,
            destination_email_address=None, notes=None):
        """
        Send satoshis to a destination address or email address.
        CB requires a fee for txns < .01 BTC, so this method will
        automatically include txn fees for those.
        """

        msg = "Can't have botha  destination email and BTC address. %s | %s" % (
                destination_email_address, destination_btc_address)
        assert not (destination_email_address and destination_btc_address), msg

        msg = 'Must send to a destination email OR BTC address'
        assert destination_email_address or destination_btc_address, msg

        dest_addr_to_use = None

        if destination_btc_address:
            dest_addr_to_use = destination_btc_address
            send_btc_dict = {'destination_btc_address': destination_btc_address}

            msg = '%s is not a valid bitcoin address' % destination_btc_address
            assert is_valid_btc_address(destination_btc_address), msg

        if destination_email_address:
            dest_addr_to_use = destination_email_address
            send_btc_dict = {'destination_email': destination_email_address}

            msg = '%s is not a valid email address' % destination_email_address
            # FIXME: implement

        btc_to_send = satoshis_to_btc(satoshis_to_send)

        SEND_URL = 'https://coinbase.com/api/v1/transactions/send_money'

        post_params = 'transaction[to]=%s&transaction[amount]=%s' % (
                dest_addr_to_use, btc_to_send)

        if satoshis_to_send < btc_to_satoshis(.01) and not destination_email_address:
            # https://coinbase.com/api/doc/1.0/transactions/send_money.html
            # Coinbase pays transaction fees on payments greater than or equal to 0.01 BTC.
            # But for smaller amounts you may want to add your own amount."
            post_params += '&transaction[user_fee]=0.0001'

        if notes:
            # TODO: url encode this?
            post_params += '&transaction[notes]=' + notes

        r = get_cb_request(
                url=SEND_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                body=post_params)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_SEND_BTC,
            url_hit=SEND_URL,
            response_code=r.status_code,
            post_params=post_params,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        success = resp_json['success']
        assert success is True, '%s: %s' % (success, resp_json.get('errors'))

        transaction = resp_json['transaction']

        recipient_address = transaction['recipient_address']
        msg = '%s != %s' % (recipient_address, dest_addr_to_use)
        assert recipient_address == dest_addr_to_use, msg

        currency = transaction['amount']['currency']
        assert currency == 'BTC', currency

        satoshis = -1 * btc_to_satoshis(transaction['amount']['amount'])

        txn_hash = transaction['hsh']

        cbs_sent_btc = CBSSentBTC.objects.create(
                transaction_id=transaction['id'],
                notes=notes)

        # Record the Send
        send_btc_dict.update({
                'credential_link': self.credentiallink,
                'cbs_sent_btc': cbs_sent_btc,
                'txn_hash': txn_hash,
                'satoshis': satoshis,
                })
        CBSSentBTC.objects.create(**send_btc_dict)

        if txn_hash:
            return BTCTransaction.objects.create(
                    txn_hash=txn_hash,
                    satoshis=satoshis,
                    conf_num=0)

    def get_new_receiving_address(self, set_as_merchant_address=False):
        """
        Generates a new receiving address
        """
        ADDRESS_URL = 'https://coinbase.com/api/v1/account/generate_receive_address'

        post_params = 'address[label]=CloseCoin %s' % now().strftime("%Y-%m-%d")

        r = get_cb_request(
                url=ADDRESS_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                body=post_params,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_NEW_ADDRESS,
            url_hit=ADDRESS_URL,
            response_code=r.status_code,
            post_params=post_params,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        assert resp_json['success'] is True, resp_json

        address = resp_json['address']

        msg = '%s is not a valid bitcoin address' % address
        assert is_valid_btc_address(address), msg

        if set_as_merchant_address:
            self.merchant.set_destination_address(address)

        return address

    def get_any_receiving_address(self, set_as_merchant_address=False):
        return self.get_new_receiving_address(set_as_merchant_address=set_as_merchant_address)


class CBSSentBTC(BaseSentBTC):
    transaction_id = models.CharField(max_length=64, blank=False, null=False, db_index=True)
    notes = models.CharField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.transaction_id)


class CBSSellBTC(BaseSellBTC):
    # Not implemented yet
    coinbase_code = models.CharField(max_length=32, blank=False, null=False, db_index=True, unique=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_btc_address or self.destination_email)
