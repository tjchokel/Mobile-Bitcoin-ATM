from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now

from credentials.models import ParentBalance, ParentSentBTC
from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

from utils import btc_to_satoshis, satoshis_to_btc

from bitstamp.client import Trading

import json


class BTSCredential(models.Model):

    username = EncryptedCharField(max_length=32, blank=False, null=False, db_index=True)
    api_key = EncryptedCharField(max_length=64, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)

    def get_trading_obj(self):
        return Trading(username=self.api_key,
                key=self.api_secret,
                secret=self.secondary_secret)

    def get_balance(self):
        """
        Return acount balance in satoshis
        """
        BALANCE_URL = 'https://www.bitstamp.net/api/balance/'
        trading_obj = self.get_trading_obj()

        try:
            balance_dict = trading_obj.account_balance()
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BALANCE,
                url_hit=BALANCE_URL,
                response_code=200,
                post_params=None,  # not accurate
                api_results=balance_dict,
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_success()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BALANCE,
                url_hit=BALANCE_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_failure()

            raise Exception(e)

        satoshis = btc_to_satoshis(balance_dict['btc_available'])

        # Record the balance results
        ParentBalance.objects.create(satoshis=satoshis,
                parent_credential=self.parentcredential)

        return satoshis

    def list_recent_transactions(self):
        '''
        Only does most recent transactions. Add pagination if you want more.

        Both BTC and USD (I think)
        '''
        LIST_TX_URL = 'https://www.bitstamp.net/api/user_transactions/'
        trading_obj = self.get_trading_obj()

        try:
            txn_list = trading_obj.user_transactions()
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_LIST_TRANSACTIONS,
                url_hit=LIST_TX_URL,
                response_code=200,
                post_params=None,  # not accurate
                api_results=str(txn_list),
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_success()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_LIST_TRANSACTIONS,
                url_hit=LIST_TX_URL,
                response_code=0,  # not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_failure()

            raise Exception(e)

        return txn_list

    def request_cashout(self, satoshis_to_sell, limit_order_price=None):
        raise Exception('Not Implemented Yet')

    def send_btc(self, satoshis_to_send, destination_btc_address):

        msg = '%s is not a valid bitcoin address' % destination_btc_address
        assert is_valid_btc_address(destination_btc_address), msg

        btc_to_send = satoshis_to_btc(satoshis_to_send)
        SEND_URL = 'https://www.bitstamp.net/api/bitcoin_withdrawal/'

        trading_obj = self.get_trading_obj()

        try:
            post_params = {'amount': btc_to_send,
                    'address': destination_btc_address}
            withdrawal_info = trading_obj.bitcoin_withdrawal(**post_params)

            withdrawal_id = withdrawal_info['id']
            msg = "%s is not an int, it's a %s" % (withdrawal_id, type(withdrawal_id))
            assert type(withdrawal_id) is int, msg

            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_SEND_BTC,
                url_hit=SEND_URL,
                response_code=200,
                post_params=post_params,
                api_results=str(withdrawal_info),
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_success()

        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_SEND_BTC,
                url_hit=SEND_URL,
                response_code=0,  # not accurate
                post_params=post_params,
                api_results=str(e),
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_failure()

            raise Exception(e)

        bts_sent_btc = BTSSentBTC.objects.create(
                withdrawal_id=withdrawal_id,
                )
        # Record the Send
        ParentSentBTC.objects.create(
                parent_credential=self.parentcredential,
                satoshis=satoshis_to_send,
                destination_btc_address=destination_btc_address,
                bts_sent_btc=bts_sent_btc,
                )

    def get_receiving_address(self, set_as_merchant_address=False):
        """
        Gets current receiving address.
        There is no way to generate a new one via API (can be done manually)
        """
        ADDRESS_URL = 'https://www.bitstamp.net/api/bitcoin_deposit_address/'
        trading_obj = self.get_trading_obj()

        try:
            address = trading_obj.bitcoin_deposit_address()

            msg = '%s is not a valid bitcoin address' % address
            assert is_valid_btc_address(address), msg

            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BTC_ADDRESS,
                url_hit=ADDRESS_URL,
                response_code=200,
                post_params=None,  # not accurate
                api_results=address,
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_success()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BTC_ADDRESS,
                url_hit=ADDRESS_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.parentcredential.merchant,
                parent_credential=self.parentcredential)

            self.parentcredential.mark_failure()

            raise Exception(e)

        if set_as_merchant_address:
            self.parentcredential.merchant.set_destination_address(address)

        return address

    def get_any_receiving_address(self, set_as_merchant_address=False):
        return self.get_receiving_address(set_as_merchant_address=set_as_merchant_address)


class BTSSentBTC(models.Model):

    BS_STATUS_CHOICES = (
        ('0', 'Open'),
        ('1', 'In Process'),
        ('2', 'Finished'),
        ('3', 'Canceled'),
        ('4', 'Failed'),
        )

    withdrawal_id = models.CharField(max_length=64, blank=False, null=False, db_index=True)
    status = models.CharField(choices=BS_STATUS_CHOICES, max_length=1,
            null=True, blank=True, db_index=True)
    # To use with polling (since we don't get this data on creation)
    status_last_checked_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.withdrawal_id)

    def check_status(self, update_results=True):
        WITHDRAWALS_URL = 'https://www.bitstamp.net/api/withdrawal_requests/'
        trading_obj = self.parentsentbtc.parent_credential.get_child_model().get_trading_obj()

        try:
            withdrawal_requests = trading_obj.withdrawal_requests()
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=200,
                post_params=None,
                api_results=json.dumps(withdrawal_requests),
                merchant=self.parentsentbtc.parent_credential.merchant,
                parent_credential=self.parentsentbtc.parent_credential)

            self.parentsentbtc.parent_credential.mark_success()

        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=0,  # not accurate
                post_params=None,
                api_results=str(e),
                merchant=self.parentsentbtc.parent_credential.merchant,
                parent_credential=self.parentsentbtc.parent_credential)

            self.parentsentbtc.parent_credential.mark_failure()

            raise Exception(e)

        for withdrawal_request in withdrawal_requests:
            if withdrawal_request['id'] == self.withdrawal_id:
                new_status = withdrawal_request['status']
                if update_results:
                    self.status = new_status
                    self.status_last_checked_at = now()
                    self.save()
                return new_status

        raise Exception('WithdrawalNotFound')
