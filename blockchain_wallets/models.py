from django_fields.fields import EncryptedCharField
from django.utils.timezone import now

from services.models import APICall
from credentials.models import BaseCredential, BaseBalance, BaseSentBTC, CredentialLink
from bitcoins.models import BTCTransaction

from bitcoins.BCAddressField import is_valid_btc_address

import requests
import json


class BCICredential(BaseCredential):

    username = EncryptedCharField(max_length=64, blank=False, null=False, db_index=True)
    main_password = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    second_password = EncryptedCharField(max_length=128, blank=True, null=True, db_index=True)

    def create_credential_link(self):
        """
        One-time method on creating a new Credential object
        Previously tried to do this by overriding the save method but it didn't work.
        """
        return CredentialLink.objects.create(bci_credential=self)

    def get_credential_abbrev(self):
        return 'BCI'

    def get_credential_to_display(self):
        return 'blockchain.info'

    def get_balance(self):
        """
        Return acount balance in satoshis
        """

        BASE_URL = 'https://blockchain.info/merchant/%s/balance?password=%s'
        BALANCE_URL = BASE_URL % (self.username, self.main_password)

        r = requests.get(BALANCE_URL)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.BLOCKCHAIN_WALLET_BALANCE,
            url_hit=BALANCE_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        if 'error' in resp_json:
            self.mark_failure()
            raise Exception('BadResponse: %s' % resp_json['error'])

        satoshis = int(resp_json['balance'])

        # Record the balance results
        BaseBalance.objects.create(satoshis=satoshis,
                credential_link=self.credentiallink)

        return satoshis

    def request_cashout(self, satoshis_to_sell, limit_order_price=None):
        raise Exception('Not Possible')

    def send_btc(self, satoshis_to_send, destination_btc_address):

        msg = '%s is not a valid bitcoin address' % destination_btc_address
        assert is_valid_btc_address(destination_btc_address), msg

        BASE_URL = 'https://blockchain.info/merchant/%s/payment?password=%s&to=%s&amount=%s&shared=false'
        SEND_URL = BASE_URL % (self.username, self.main_password,
                destination_btc_address, satoshis_to_send)

        if self.second_password:
            SEND_URL += '&second_password=%s' % self.second_password

        r = requests.get(SEND_URL)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.BLOCKCHAIN_WALLET_SEND_BTC,
            url_hit=SEND_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        tx_hash = resp_json['tx_hash']

        assert 'error' not in resp_json, resp_json

        # Record the Send
        BCISentBTC.objects.create(
                credential_link=self.credentiallink,
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
        ADDRESS_URL = BASE_URL % (self.username, self.main_password, label)

        r = requests.get(url=ADDRESS_URL)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.BLOCKCHAIN_WALLET_NEW_ADDRESS,
            url_hit=ADDRESS_URL,
            response_code=r.status_code,
            post_params=None,
            api_results=r.content,
            merchant=self.merchant,
            credential_link=self.credentiallink)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        address = resp_json['address']

        msg = '%s is not a valid bitcoin address' % address
        assert is_valid_btc_address(address), msg

        if set_as_merchant_address:
            self.merchant.set_destination_address(address)

        return address

    def get_any_receiving_address(self, set_as_merchant_address=False):
        return self.get_new_receiving_address(set_as_merchant_address=set_as_merchant_address)


class BCISentBTC(BaseSentBTC):
    " No new model fields "

    def __str__(self):
        return '%s: %s' % (self.id, self.transaction_id)
