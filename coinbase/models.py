from django.db import models
from django_fields.fields import EncryptedCharField

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address
from coinbase.api import get_cb_request

from utils import btc_to_satoshis, satoshis_to_btc

from countries import BFH_CURRENCY_DROPDOWN

from dateutil import parser

import json


class APICredential(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    # Both of these are extra-long for safety
    api_key = EncryptedCharField(max_length=64, blank=True, null=True, db_index=True)
    api_secret = EncryptedCharField(max_length=128, blank=True, null=True, db_index=True)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s from %s' % (self.id, self.merchant.business_name)

    def get_balance(self):
        """
        Return acount balance in satoshis
        """
        BALANCE_URL = 'https://coinbase.com/api/v1/account/balance'
        content, status_code = get_cb_request(
                url=BALANCE_URL,
                api_key=self.api_key,
                api_secret=self.api_secret)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_BALANCE,
            url_hit=BALANCE_URL,
            response_code=status_code,
            post_params=None,
            api_results=content,
            merchant=self.merchant)

        err_msg = 'Expected status code 200 but got %s' % status_code
        assert status_code == 200, err_msg

        resp_json = json.loads(content)

        currency_returned = resp_json['currency']
        assert currency_returned == 'BTC', currency_returned

        satoshis = btc_to_satoshis(resp_json['amount'])

        # Record the balance results
        CurrentBalance.objects.create(satoshis=satoshis, api_credential=self)

        return satoshis

    def list_recent_purchases_and_sales(self):
        LIST_FIAT_URL = 'https://coinbase.com/api/v1/transfers'

        url_to_hit = LIST_FIAT_URL+'?limit=100'

        content, status_code = get_cb_request(
                url=url_to_hit,
                api_key=self.api_key,
                api_secret=self.api_secret,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_LIST_PURCHASE_SALE,
            url_hit=url_to_hit,
            response_code=status_code,
            api_results=content,
            merchant=self.merchant)

        err_msg = 'Expected status code 200 but got %s' % status_code
        assert status_code == 200, err_msg

        return json.loads(content)['transfers']

    def list_recent_btc_transactions(self):
        ''' Limits to 30, add pagination if you want more '''
        LIST_TX_URL = 'https://coinbase.com/api/v1/transactions'

        content, status_code = get_cb_request(
                url=LIST_TX_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_LIST_BTC_TRANSACTIONS,
            url_hit=LIST_TX_URL,
            response_code=status_code,
            post_params=None,
            api_results=content,
            merchant=self.merchant)

        err_msg = 'Expected status code 200 but got %s' % status_code
        assert status_code == 200, err_msg

        json_resp = json.loads(content)

        # Record the balance
        CurrentBalance.objects.create(
                satoshis=btc_to_satoshis(json_resp['balance']['amount']),
                api_credential=self,
                )

        # Return transactions
        return json_resp['transactions']

    def request_cashout(self, satoshis_to_sell):
        SELL_URL = 'https://coinbase.com/api/v1/sells'
        btc_to_sell = satoshis_to_btc(satoshis_to_sell)
        url_to_hit = SELL_URL + '?qty=%s' % btc_to_sell

        content, status_code = get_cb_request(
                url=url_to_hit,
                api_key=self.api_key,
                api_secret=self.api_secret,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_BALANCE,
            url_hit=url_to_hit,
            response_code=status_code,
            api_results=content,
            merchant=self.merchant)

        err_msg = 'Expected status code 200 but got %s' % status_code
        assert status_code == 200, err_msg

        resp_json = json.loads(content)

        success = resp_json['success']
        assert success is True, '%s: %s' % (success, resp_json.get('errors'))

        transfer = resp_json['transfer']

        status = transfer['status']
        assert status == 'created', status

        btc_obj = transfer['btc']
        assert btc_obj['currency'] == 'BTC', btc_obj

        satoshis = btc_to_satoshis(btc_obj['amount'])
        assert satoshis == satoshis_to_sell, btc_obj['amount']

        currency_to_recieve = transfer['total']['currency']

        fiat_fees_in_cents = 0
        for fee in transfer['fees']:
            fiat_fees_in_cents += int(fee['cents'])
            msg = '%s != %s' % (fee['currency_iso'], currency_to_recieve)
            assert fee['currency_iso'] == currency_to_recieve, msg
        fiat_fees = fiat_fees_in_cents/100.0

        SellOrder.objects.create(
                api_credential=self,
                cb_code=transfer['code'],
                received_at=parser.parse(transfer['created_at']),
                satoshis=satoshis,
                currency_code=currency_to_recieve,
                fiat_fees=fiat_fees,
                fiat_to_receive=float(transfer['total']['amount']),
        )

        return resp_json

    def send_btc(self, satoshis_to_send, destination_address, notes=None, user_fee=None):

        msg = '%s is not a valid bitcoin address' % destination_address
        assert is_valid_btc_address(destination_address), msg

        btc_to_send = satoshis_to_btc(satoshis_to_send)

        SEND_URL = 'https://coinbase.com/api/v1/transactions/send_money'

        post_params = 'transaction[to]=%s&transaction[amount]=%s' % (
                destination_address, btc_to_send)

        if user_fee:
            post_params += '&transaction[user_fee]=' + user_fee

        if notes:
            # TODO: url encode this?
            post_params += '&transaction[notes]=' + notes

        content, status_code = get_cb_request(
                url=SEND_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                body=post_params)

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_SEND_BTC,
            url_hit=SEND_URL,
            response_code=status_code,
            post_params=post_params,
            api_results=content,
            merchant=self.merchant)

        err_msg = 'Expected status code 200 but got %s' % status_code
        assert status_code == 200, err_msg

        resp_json = json.loads(content)

        success = resp_json['success']
        assert success is True, '%s: %s' % (success, resp_json.get('errors'))

        transaction = resp_json['transaction']

        recipient_address = transaction['recipient_address']
        msg = '%s != %s' % (recipient_address, destination_address)
        assert recipient_address == destination_address, msg

        currency = transaction['amount']['currency']
        assert currency == 'BTC', currency

        satoshis = btc_to_satoshis(transaction['amount']['amount'])

        # Record the Send
        SendBTC.objects.create(
                api_credential=self,
                recieved_at=parser.parse(transaction['created_at']),
                txn_hash=transaction['hsh'],
                satoshis=satoshis,
                destination_address=destination_address,
                cb_id=transaction['id'],
                notes=notes)

        return resp_json


class SellOrder(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    api_credential = models.ForeignKey(APICredential, blank=False, null=False)
    # The txn that caused this event (may be blank)
    btc_transaction = models.ForeignKey('bitcoins.BTCTransaction', blank=True, null=True)
    # info returned
    cb_code = models.CharField(max_length=32, blank=False, null=False, db_index=True)
    received_at = models.DateTimeField(blank=False, null=False, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    currency_code = models.CharField(max_length=5, blank=False, null=False,
            db_index=True, choices=BFH_CURRENCY_DROPDOWN)
    # CB and related bank fees
    fees_in_fiat = models.DecimalField(blank=False, null=False, max_digits=10,
            decimal_places=2, db_index=True)
    # what's received by user after CB fees
    to_receive_in_fiat = models.DecimalField(blank=False, null=False,
            max_digits=10, decimal_places=2, db_index=True)


class CurrentBalance(models.Model):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    api_credential = models.ForeignKey(APICredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)


class SendBTC(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    api_credential = models.ForeignKey(APICredential, blank=False, null=False)
    received_at = models.DateTimeField(blank=False, null=False, db_index=True)
    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_address = models.CharField(max_length=34, blank=False,
            null=False, db_index=True)
    cb_id = models.CharField(max_length=64, blank=False, null=False, db_index=True)
    notes = models.CharField(max_length=2048, blank=False, null=False)
