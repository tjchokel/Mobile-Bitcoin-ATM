from credentials.base import BaseCredential

from django.utils.timezone import now

from services.models import APICall
from credentials.models import CurrentBalance, SentBTC
from bitcoins.models import BTCTransaction

from bitcoins.BCAddressField import is_valid_btc_address

import requests
import json


class BCICredential(BaseCredential):

    def get_balance(self):
        """
        Return acount balance in satoshis
        """

        BASE_URL = 'https://blockchain.info/merchant/%s/balance?password=%s'
        BALANCE_URL = BASE_URL % (self.cred.api_key, self.cred.api_secret)

        r = requests.get(BALANCE_URL)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.BLOCKCHAIN_WALLET_BALANCE,
            url_hit=BALANCE_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.cred.merchant,
            )

        if r.status_code == 200:
            self.cred.last_failed_at = None
            self.cred.last_succeded_at = now()
            self.cred.save()
        else:
            self.cred.last_failed_at = now()
            self.cred.save()
            err_msg = 'Expected status code 200 but got %s' % r.status_code
            raise Exception('StatusCode: %s' % err_msg)

        resp_json = json.loads(r.content)

        if 'error' in resp_json:
            self.cred.last_failed_at = now()
            self.cred.save()
            raise Exception('BadResponse: %s' % resp_json['error'])

        satoshis = int(resp_json['balance'])

        # Record the balance results
        CurrentBalance.objects.create(satoshis=satoshis, credential=self.cred)

        return satoshis

    def request_cashout(self, satoshis_to_sell, limit_order_price=None):
        raise Exception('Not Possible')

    def send_btc(self, satoshis_to_send, destination_btc_address):

        msg = '%s is not a valid bitcoin address' % destination_btc_address
        assert is_valid_btc_address(destination_btc_address), msg

        BASE_URL = 'https://blockchain.info/merchant/%s/payment?password=%s&to=%s&amount=%s&shared=false'
        SEND_URL = BASE_URL % (self.cred.api_key, self.cred.api_secret,
                destination_btc_address, satoshis_to_send)

        if self.cred.secondary_secret:
            SEND_URL += '&second_password=%s' % self.cred.secondary_secret

        r = requests.get(SEND_URL)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.BLOCKCHAIN_WALLET_SEND_BTC,
            url_hit=SEND_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.cred.merchant,
            )

        if r.status_code == 200:
            self.cred.last_failed_at = None
            self.cred.last_succeded_at = now()
            self.cred.save()
        else:
            self.cred.last_failed_at = now()
            self.cred.save()
            err_msg = 'Expected status code 200 but got %s' % r.status_code
            raise Exception('StatusCode: %s' % err_msg)

        resp_json = json.loads(r.content)

        tx_hash = resp_json['tx_hash']

        assert 'error' not in resp_json, resp_json

        # Record the Send
        SentBTC.objects.create(
                credential=self.cred,
                satoshis=satoshis_to_send,
                destination_btc_address=destination_btc_address,
                txn_hash=tx_hash,
                )

        return BTCTransaction.objects.create(
            txn_hash=tx_hash,
            satoshis=satoshis_to_send,
            conf_num=0)

    def get_new_receiving_address(self, set_as_merchant_address=False):
        """
        Generates a new receiving address
        """
        label = 'CloseCoin %s' % now().strftime("%Y-%m-%d")

        BASE_URL = 'https://blockchain.info/merchant/%s/new_address?password=%s&label=%s'
        ADDRESS_URL = BASE_URL % (self.cred.api_key, self.cred.api_secret, label)

        r = requests.get(url=ADDRESS_URL)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.BLOCKCHAIN_WALLET_NEW_ADDRESS,
            url_hit=ADDRESS_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.cred.merchant)

        if r.status_code == 200:
            self.cred.last_failed_at = None
            self.cred.last_succeded_at = now()
            self.cred.save()
        else:
            self.cred.last_failed_at = now()
            self.cred.save()
            err_msg = 'Expected status code 200 but got %s' % r.status_code
            raise Exception('StatusCode: %s' % err_msg)

        resp_json = json.loads(r.content)

        address = resp_json['address']

        msg = '%s is not a valid bitcoin address' % address
        assert is_valid_btc_address(address), msg

        if set_as_merchant_address:
            self.cred.merchant.set_destination_address(address)

        return address

    def get_any_receiving_address(self, set_as_merchant_address=False):
        return self.get_new_receiving_address(set_as_merchant_address=set_as_merchant_address)
