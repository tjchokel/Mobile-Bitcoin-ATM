from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address
from bitcoins.models import BTCTransaction

import requests
import json


class BCICredential(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    # These are extra-long for safety
    # username is sometimes referred to as $guid in BCI docs
    username = EncryptedCharField(max_length=64, blank=False, null=False, db_index=True)
    main_password = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    second_password = EncryptedCharField(max_length=128, blank=True, null=True, db_index=True)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s from %s' % (self.id, self.merchant.business_name)

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
            )

        if r.status_code == 200:
            self.last_failed_at = None
            self.last_succeded_at = now()
            self.save()
        else:
            self.last_failed_at = now()
            self.save()
            err_msg = 'Expected status code 200 but got %s' % r.status_code
            raise Exception('StatusCode: %s' % err_msg)

        resp_json = json.loads(r.content)

        if 'error' in resp_json:
            self.last_failed_at = now()
            self.save()
            raise Exception('BadResponse: %s' % resp_json['error'])

        satoshis = int(resp_json['balance'])

        # Record the balance results
        BCIBalance.objects.create(satoshis=satoshis, bci_credential=self)

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
            )

        if r.status_code == 200:
            self.last_failed_at = None
            self.last_succeded_at = now()
            self.save()
        else:
            self.last_failed_at = now()
            self.save()
            err_msg = 'Expected status code 200 but got %s' % r.status_code
            raise Exception('StatusCode: %s' % err_msg)

        resp_json = json.loads(r.content)

        tx_hash = resp_json['tx_hash']

        assert 'error' not in resp_json, resp_json

        # Record the Send
        BCISendBTC.objects.create(
                bci_credential=self,
                satoshis=satoshis_to_send,
                destination_address=destination_btc_address,
                tx_hash=tx_hash,
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
            merchant=self.merchant)

        if r.status_code == 200:
            self.last_failed_at = None
            self.last_succeded_at = now()
            self.save()
        else:
            self.last_failed_at = now()
            self.save()
            err_msg = 'Expected status code 200 but got %s' % r.status_code
            raise Exception('StatusCode: %s' % err_msg)

        resp_json = json.loads(r.content)

        address = resp_json['address']

        msg = '%s is not a valid bitcoin address' % address
        assert is_valid_btc_address(address), msg

        if set_as_merchant_address:
            self.merchant.set_destination_address(address)

        return address

    def get_status(self):
        if self.last_failed_at:
            return _('Invalid')
        else:
            return _('Valid')


class BCIBalance(models.Model):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    bci_credential = models.ForeignKey(BCICredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.satoshis)


class BCISendBTC(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    bci_credential = models.ForeignKey(BCICredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_address = models.CharField(max_length=34, blank=False,
            null=False, db_index=True)
    tx_hash = models.CharField(max_length=64, blank=False, null=False,
            unique=True, db_index=True)

    def __str__(self):
        return '%s: %s to %s' % (self.id, self.satoshis, self.destination_address)
