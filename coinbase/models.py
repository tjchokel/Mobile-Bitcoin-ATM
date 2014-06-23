from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address
from coinbase.api import get_cb_request

from utils import btc_to_satoshis, satoshis_to_btc

from countries import BFH_CURRENCY_DROPDOWN

from dateutil import parser

import json


class CBCredential(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    # Both of these are extra-long for safety
    api_key = EncryptedCharField(max_length=64, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # Not implemented anywhere:
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s from %s' % (self.id, self.merchant.business_name)

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
            merchant=self.merchant)

        if r.status_code != 200:
            self.last_failed_at = now()
        else:
            self.last_failed_at = None
        self.save()

        err_msg = 'Expected status code 200 but got %s' % r.status_code
        assert r.status_code == 200, err_msg
        self.last_succeded_at = now()
        self.save()

        resp_json = json.loads(r.content)

        currency_returned = resp_json['currency']
        assert currency_returned == 'BTC', currency_returned

        satoshis = btc_to_satoshis(resp_json['amount'])

        # Record the balance results
        CurrentBalance.objects.create(satoshis=satoshis, cb_credential=self)

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
            merchant=self.merchant)

        if r.status_code != 200:
            self.last_failed_at = now()
        else:
            self.last_failed_at = None
        self.save()

        err_msg = 'Expected status code 200 but got %s' % r.status_code
        assert r.status_code == 200, err_msg
        self.last_succeded_at = now()
        self.save()

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
            merchant=self.merchant)

        if r.status_code != 200:
            self.last_failed_at = now()
        else:
            self.last_failed_at = None
        self.save()

        err_msg = 'Expected status code 200 but got %s' % r.status_code
        assert r.status_code == 200, err_msg

        json_resp = json.loads(r.content)

        # Record the balance
        CurrentBalance.objects.create(
                satoshis=btc_to_satoshis(json_resp['balance']['amount']),
                cb_credential=self,
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
            merchant=self.merchant)

        if r.status_code != 200:
            self.last_failed_at = now()
        else:
            self.last_failed_at = None
        self.save()

        err_msg = 'Expected status code 200 but got %s' % r.status_code
        assert r.status_code == 200, err_msg

        self.last_succeded_at = now()
        self.save()

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

        return SellOrder.objects.create(
                cb_credential=self,
                cb_code=transfer['code'],
                received_at=parser.parse(transfer['created_at']),
                satoshis=satoshis,
                currency_code=currency_to_recieve,
                fees_in_fiat=fiat_fees,
                to_receive_in_fiat=float(transfer['total']['amount']),
                )

    def send_btc(self, satoshis_to_send, destination_btc_address,
            destination_email_address=None, notes=None):
        """
        Send satoshis to a destination address or email address.
        CB requires a fee for txns < .01 BTC, so it will automatically include
        txn fees for those.
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
            # FIXME

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
            merchant=self.merchant)

        if r.status_code != 200:
            self.last_failed_at = now()
        else:
            self.last_failed_at = None
        self.save()

        err_msg = 'Expected status code 200 but got %s' % r.status_code
        assert r.status_code == 200, err_msg

        self.last_succeded_at = now()
        self.save()

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

        # Record the Send
        send_btc_dict.update({
                'cb_credential': self,
                'received_at': parser.parse(transaction['created_at']),
                'txn_hash': transaction['hsh'],
                'satoshis': satoshis,
                'cb_id': transaction['id'],
                'notes': notes,
                })
        return SendBTC.objects.create(**send_btc_dict)

    def get_status(self):
        if self.last_failed_at:
            return _('Invalid')
        else:
            return _('Valid')


class SellOrder(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cb_credential = models.ForeignKey(CBCredential, blank=False, null=False)
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

    def __str__(self):
        return '%s: %s' % (self.id, self.cb_code)


class CurrentBalance(models.Model):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cb_credential = models.ForeignKey(CBCredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.satoshis)


class SendBTC(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    cb_credential = models.ForeignKey(CBCredential, blank=False, null=False)
    received_at = models.DateTimeField(blank=False, null=False, db_index=True)
    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_btc_address = models.CharField(max_length=34, blank=True,
            null=True, db_index=True)
    destination_email = models.EmailField(blank=True, null=True, db_index=True)
    cb_id = models.CharField(max_length=64, blank=False, null=False, db_index=True)
    notes = models.CharField(max_length=2048, blank=False, null=False)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_email or self.destination_btc_address)
