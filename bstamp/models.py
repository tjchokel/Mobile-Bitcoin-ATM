from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

from utils import btc_to_satoshis, satoshis_to_btc

from bitstamp.client import Trading


class BSCredential(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    # Both of these are extra-long for safety
    username = EncryptedCharField(max_length=32, blank=False, null=False, db_index=True)
    api_key = EncryptedCharField(max_length=64, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s from %s' % (self.id, self.merchant.business_name)

    def get_trading_obj(self):
        return Trading(username=self.username, key=self.api_key, secret=self.api_secret)

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
                merchant=self.merchant)

            self.last_succeded_at = now()
            self.last_failed_at = None
            self.save()
        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BALANCE,
                url_hit=BALANCE_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.merchant)

            self.last_failed_at = now()
            self.save()

            raise Exception(e)

        satoshis = btc_to_satoshis(balance_dict['btc_available'])

        # Record the balance results
        BSBalance.objects.create(satoshis=satoshis, bs_credential=self)

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
                merchant=self.merchant)

            self.last_succeded_at = now()
            self.last_failed_at = None
            self.save()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_LIST_TRANSACTIONS,
                url_hit=LIST_TX_URL,
                response_code=0,  # not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.merchant)

            self.last_failed_at = now()
            self.save()

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
                merchant=self.merchant)

            self.last_succeded_at = now()
            self.last_failed_at = None
            self.save()

        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_SEND_BTC,
                url_hit=SEND_URL,
                response_code=0,  # not accurate
                post_params=post_params,
                api_results=str(e),
                merchant=self.merchant)

            self.last_failed_at = now()
            self.save()

            raise Exception(e)

        # Record the Send
        return BSSendBTC.objects.create(
                bs_credential=self,
                bs_withdrawal_id=withdrawal_id,
                satoshis=satoshis_to_send,
                destination_address=destination_btc_address,
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
                merchant=self.merchant)

            self.last_succeded_at = now()
            self.save()
        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BTC_ADDRESS,
                url_hit=ADDRESS_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.merchant)

            self.last_failed_at = now()
            self.save()

            raise Exception(e)

        if set_as_merchant_address:
            self.merchant.set_destination_address(address)

        return address

    def get_status(self):
        if self.last_failed_at:
            return _('Invalid')
        else:
            return _('Valid')


class BSBalance(models.Model):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    bs_credential = models.ForeignKey(BSCredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.satoshis)


class BSSendBTC(models.Model):

    BS_STATUS_CHOICES = (
            (0, 'Open'),
            (1, 'In Process'),
            (2, 'Finished'),
            (3, 'Canceled'),
            (4, 'Failed'),
            )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    bs_credential = models.ForeignKey(BSCredential, blank=False, null=False)
    bs_withdrawal_id = models.BigIntegerField(blank=False, null=False, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_address = models.CharField(max_length=34, blank=False,
            null=False, db_index=True)
    # To use with polling (we don't get this data on creation)
    status = models.CharField(choices=BS_STATUS_CHOICES, max_length=1,
            null=True, blank=True, db_index=True)
    status_last_checked_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_address)

    def check_status(self, update_results=True):
        WITHDRAWALS_URL = 'https://www.bitstamp.net/api/withdrawal_requests/'
        trading_obj = self.bs_credential.get_trading_obj()

        try:
            withdrawal_requests = trading_obj.withdrawal_requests()
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=200,
                post_params=None,
                api_results=str(withdrawal_requests),
                merchant=self.bs_credential.merchant)

            self.last_succeded_at = now()
            self.last_failed_at = None
            self.save()
        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=0,  # not accurate
                post_params=None,
                api_results=str(e),
                merchant=self.bs_credential.merchant)
            self.last_failed_at = now()
            self.save()
            raise Exception(e)

        for withdrawal_request in withdrawal_requests:
            if withdrawal_request['id'] == self.bs_withdrawal_id:
                new_status = int(withdrawal_request['status'])
                if update_results:
                    self.status = new_status
                    self.status_last_checked_at = now()
                    self.save()
                return new_status

        raise Exception('WithdrawalNotFound')
