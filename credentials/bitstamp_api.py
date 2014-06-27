from credentials.base import BaseCredential

from django.utils.timezone import now

from credentials.models import CurrentBalance, SentBTC

from services.models import APICall

from bitcoins.BCAddressField import is_valid_btc_address

from utils import btc_to_satoshis, satoshis_to_btc

from bitstamp.client import Trading


class BTSCredential(BaseCredential):

    def get_trading_obj(self):
        return Trading(username=self.cred.api_key,
                key=self.cred.api_secret,
                secret=self.cred.secondary_secret)

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
                merchant=self.cred.merchant)

            self.cred.last_succeded_at = now()
            self.cred.last_failed_at = None
            self.cred.save()
        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BALANCE,
                url_hit=BALANCE_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.cred.merchant)

            self.cred.last_failed_at = now()
            self.cred.save()

            raise Exception(e)

        satoshis = btc_to_satoshis(balance_dict['btc_available'])

        # Record the balance results
        CurrentBalance.objects.create(satoshis=satoshis, credential=self.cred)

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
                merchant=self.cred.merchant)

            self.cred.last_succeded_at = now()
            self.cred.last_failed_at = None
            self.cred.save()

        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_LIST_TRANSACTIONS,
                url_hit=LIST_TX_URL,
                response_code=0,  # not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.cred.merchant)

            self.cred.last_failed_at = now()
            self.cred.save()

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
                merchant=self.cred.merchant)

            self.cred.last_succeded_at = now()
            self.cred.last_failed_at = None
            self.cred.save()

        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_SEND_BTC,
                url_hit=SEND_URL,
                response_code=0,  # not accurate
                post_params=post_params,
                api_results=str(e),
                merchant=self.cred.merchant)

            self.cred.last_failed_at = now()
            self.cred.save()

            raise Exception(e)

        # Record the Send
        SentBTC.objects.create(
                credential=self.cred,
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
                merchant=self.cred.merchant)

            self.cred.last_succeded_at = now()
            self.cred.save()
        except Exception as e:
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_BTC_ADDRESS,
                url_hit=ADDRESS_URL,
                response_code=0,  # this is not accurate
                post_params=None,  # not accurate
                api_results=str(e),
                merchant=self.cred.merchant)

            self.cred.last_failed_at = now()
            self.cred.save()

            raise Exception(e)

        if set_as_merchant_address:
            self.cred.merchant.set_destination_address(address)

        return address

    def check_status(self, update_results=True):
        WITHDRAWALS_URL = 'https://www.bitstamp.net/api/withdrawal_requests/'
        trading_obj = self.get_trading_obj()

        try:
            withdrawal_requests = trading_obj.withdrawal_requests()
            # Log the API call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=200,
                post_params=None,
                api_results=str(withdrawal_requests),
                merchant=self.cred.merchant)

            self.cred.last_succeded_at = now()
            self.cred.last_failed_at = None
            self.cred.save()
        except Exception as e:
            # Log the API Call
            APICall.objects.create(
                api_name=APICall.BITSTAMP_WITHDRAWALS,
                url_hit=WITHDRAWALS_URL,
                response_code=0,  # not accurate
                post_params=None,
                api_results=str(e),
                merchant=self.cred.merchant)
            self.cred.last_failed_at = now()
            self.cred.save()
            raise Exception(e)

        for withdrawal_request in withdrawal_requests:
            if withdrawal_request['id'] == self.cred.bs_withdrawal_id:
                new_status = withdrawal_request['status']
                if update_results:
                    self.cred.status = new_status
                    self.cred.status_last_checked_at = now()
                    self.cred.save()
                return new_status

        raise Exception('WithdrawalNotFound')
