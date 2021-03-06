from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now

from credentials.models import BaseCredential, BaseBalance, BaseSentBTC, BaseAddressFromCredential
from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

from utils import btc_to_satoshis, satoshis_to_btc

from bitstamp.client import Trading

import json


class BTSCredential(BaseCredential):

    customer_id = EncryptedCharField(max_length=32, blank=False, null=False, db_index=True)
    api_key = EncryptedCharField(max_length=64, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)

    def get_credential_abbrev(self):
        return 'BTS'

    def get_credential_to_display(self):
        return 'BitStamp'

    def get_login_link(self):
        return 'https://www.bitstamp.net/account/login/'

    def is_bitstamp_credential(self):
        return True

    def get_trading_obj(self):
        return Trading(username=self.customer_id, key=self.api_key, secret=self.api_secret)

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
                merchant=self.merchant,
                credential=self)

            self.mark_success()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BALANCE,
                url_hit=BALANCE_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.merchant,
                credential=self)

            self.mark_failure()
            print 'Error was: %s' % e
            return False

        satoshis = btc_to_satoshis(balance_dict['btc_available'])

        # Record the balance results
        BaseBalance.objects.create(satoshis=satoshis,
                credential=self)

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
                merchant=self.merchant,
                credential=self)

            self.mark_success()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_LIST_TRANSACTIONS,
                url_hit=LIST_TX_URL,
                response_code=0,  # not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.merchant,
                credential=self)

            self.mark_failure()
            print 'Error was: %s' % e

        return txn_list

    def request_cashout(self, satoshis_to_sell, limit_order_price=None):
        raise Exception('Not Implemented Yet')

    def send_btc(self, satoshis_to_send, destination_btc_address):
        """
        Returns a tuple of the form (some or all may be none):
            btc_txn, sent_btc_obj, api_call, err_str
        """

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
            api_call = APICall.objects.create(
                api_name=APICall.BITSTAMP_SEND_BTC,
                url_hit=SEND_URL,
                response_code=200,
                post_params=post_params,
                api_results=str(withdrawal_info),
                merchant=self.merchant,
                credential=self)

            self.mark_success()

        except Exception as e:
            # Log the API Call
            api_call = APICall.objects.create(
                api_name=APICall.BITSTAMP_SEND_BTC,
                url_hit=SEND_URL,
                response_code=0,  # not accurate
                post_params=post_params,
                api_results=str(e),
                merchant=self.merchant,
                credential=self)

            self.mark_failure()
            print 'Error was: %s' % e
            # TODO: this assumes all error messages here are safe to display to the user
            return None, None, api_call, str(e)

        sent_btc_obj = BTSSentBTC.objects.create(
                credential=self,
                satoshis=satoshis_to_send,
                destination_btc_address=destination_btc_address,
                withdrawal_id=withdrawal_id,
                status='0',
                )

        # This API doesn't return a TX hash on sending bitcoin :(
        return None, sent_btc_obj, api_call, None

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
                merchant=self.merchant,
                credential=self)

            BaseAddressFromCredential.objects.create(
                    credential=self,
                    b58_address=address,
                    retired_at=None)

            self.mark_success()

            if set_as_merchant_address:
                self.merchant.set_destination_address(dest_address=address,
                        credential_used=self)

            return address

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BTC_ADDRESS,
                url_hit=ADDRESS_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.merchant,
                credential=self)

            self.mark_failure()

            print 'Error was: %s' % e

            return None

    def get_best_receiving_address(self, set_as_merchant_address=False):
        " Get existing receiving address (no way to get a new one with BTS) "
        return self.get_receiving_address(set_as_merchant_address=set_as_merchant_address)


class BTSSentBTC(BaseSentBTC):

    STATUS_CHOICES = (
        ('0', 'Open'),
        ('1', 'In Process'),
        ('2', 'Finished'),
        ('3', 'Canceled'),
        ('4', 'Failed'),
        )

    # warning, these may not correspond to the ids that `list_recent_transactions` returns

    withdrawal_id = models.CharField(max_length=64, blank=False, null=False, db_index=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=1,
            null=True, blank=True, db_index=True)
    # To use with polling (since we don't get this data on creation)
    status_last_checked_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.withdrawal_id)

    def check_status(self, update_results=True):
        WITHDRAWALS_URL = 'https://www.bitstamp.net/api/withdrawal_requests/'
        trading_obj = self.get_credential().get_trading_obj()

        try:
            withdrawal_requests = trading_obj.withdrawal_requests()
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=200,
                post_params=None,
                api_results=json.dumps(withdrawal_requests),
                merchant=self.get_credential().merchant,
                credential=self.credential,
                )

            self.credential.mark_success()

        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=0,  # not accurate
                post_params=None,
                api_results=str(e),
                merchant=self.get_credential().merchant,
                credential=self.credential,
                )

            self.credential.mark_failure()
            print 'Error was: %s' % e

        for withdrawal_request in withdrawal_requests:
            if withdrawal_request['id'] == self.withdrawal_id:
                new_status = withdrawal_request['status']
                if update_results:
                    self.status = new_status
                    self.status_last_checked_at = now()
                    self.save()
                return new_status

        raise Exception('WithdrawalNotFound')
