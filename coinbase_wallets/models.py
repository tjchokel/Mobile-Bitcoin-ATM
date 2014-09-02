from django.db import models
from django_fields.fields import EncryptedCharField
from django.utils.timezone import now

from credentials.models import BaseCredential, BaseBalance, BaseSentBTC, BaseSellBTC, BaseAddressFromCredential
from services.models import APICall
from bitcoins.models import BTCTransaction

from coinbase_wallets.api import get_cb_request

from bitcoins.BCAddressField import is_valid_btc_address

from utils import btc_to_satoshis, satoshis_to_btc

import json


class CBSCredential(BaseCredential):

    api_key = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=256, blank=False, null=False, db_index=True)

    def get_credential_abbrev(self):
        return 'CBS'

    def get_credential_to_display(self):
        return 'Coinbase'

    def get_login_link(self):
        return 'https://coinbase.com/signin'

    def is_coinbase_credential(self):
        return True

    def get_balance(self):
        """
        Return acount balance in satoshis

        We return False when there's an API fail
        This prevents the front-end from breaking while still passing the neccessary info back

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
            credential=self)

        status_code_is_valid = self.handle_status_code(r.status_code)

        if not status_code_is_valid:
            return False

        resp_json = json.loads(r.content)

        if 'currency' not in resp_json and resp_json['currency'] != 'BTC':
            self.mark_failure()
            return False

        satoshis = btc_to_satoshis(resp_json['amount'])

        # Record the balance results
        BaseBalance.objects.create(satoshis=satoshis, credential=self)

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
            credential=self)

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
            credential=self)

        self.handle_status_code(r.status_code)

        json_resp = json.loads(r.content)

        # Record the balance
        BaseBalance.objects.create(
                satoshis=btc_to_satoshis(json_resp['balance']['amount']),
                credential=self
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
            post_params={'qty': btc_to_sell},
            merchant=self.merchant,
            credential=self)

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
                credential=self,
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
        CB requires a fee for txns < .001 BTC, so this method will
        automatically include txn fees for those.

        Returns a tuple of the form (some or all may be none):
            btc_txn, sent_btc_obj, api_call, err_str
        """

        msg = "Can't have both a destination email and BTC address. %s | %s" % (
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

        body = 'transaction[to]=%s&transaction[amount]=%s' % (
                dest_addr_to_use, btc_to_send)
        post_params = {'to': dest_addr_to_use, 'amount': btc_to_send}

        if satoshis_to_send <= btc_to_satoshis(.001) and not destination_email_address:
            # https://coinbase.com/api/doc/1.0/transactions/send_money.html
            # Coinbase pays transaction fees on payments greater than or equal to 0.001 BTC.
            # But for smaller amounts you have to add your own
            # For some reason, coinbase requires 2x fees of .2 mBTC vs (.1 mBTC)
            body += '&transaction[user_fee]=0.0002'
            post_params['user_fee'] = 0.0002

        if notes:
            # TODO: url encode this?
            body += '&transaction[notes]=' + notes
            post_params['notes'] = notes

        r = get_cb_request(
                url=SEND_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                body=body)

        # Log the API call
        api_call = APICall.objects.create(
            api_name=APICall.COINBASE_SEND_BTC,
            url_hit=SEND_URL,
            response_code=r.status_code,
            post_params=post_params,
            api_results=r.content,
            merchant=self.merchant,
            credential=self)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        if resp_json.get('error') or resp_json.get('errors'):
            err_str = resp_json.get('error')
            # combine the two
            if resp_json.get('errors'):
                if err_str:
                    err_str += ' %s' % resp_json.get('errors')
                else:
                    err_str = resp_json.get('errors')

            # this assumes all error messages here are safe to display to the user
            return None, None, api_call, err_str

        transaction = resp_json['transaction']

        satoshis = -1 * btc_to_satoshis(transaction['amount']['amount'])

        txn_hash = transaction['hsh']

        # Record the Send
        send_btc_dict.update({
                'credential': self,
                'txn_hash': txn_hash,
                'satoshis': satoshis,
                'transaction_id': transaction['id'],
                'notes': notes,
                })
        sent_btc_obj = CBSSentBTC.objects.create(**send_btc_dict)

        if txn_hash:
            return BTCTransaction.objects.create(
                    txn_hash=txn_hash,
                    satoshis=satoshis,
                    conf_num=0), sent_btc_obj, api_call, None
        else:
            # Coinbase seems finicky about transaction hashes
            return None, sent_btc_obj, api_call, None

    def get_new_receiving_address(self, set_as_merchant_address=False):
        """
        Generates a new receiving address
        """
        ADDRESS_URL = 'https://coinbase.com/api/v1/account/generate_receive_address'

        label = 'CoinSafe Address %s' % now().strftime("%Y-%m-%d %H:%M:%S")
        body = 'address[label]=%s' % label

        r = get_cb_request(
                url=ADDRESS_URL,
                api_key=self.api_key,
                api_secret=self.api_secret,
                body=body,
                )

        # Log the API call
        APICall.objects.create(
            api_name=APICall.COINBASE_NEW_ADDRESS,
            url_hit=ADDRESS_URL,
            response_code=r.status_code,
            post_params={'label': label},
            api_results=r.content,
            merchant=self.merchant,
            credential=self)

        self.handle_status_code(r.status_code)

        resp_json = json.loads(r.content)

        assert resp_json['success'] is True, resp_json

        address = resp_json['address']

        msg = '%s is not a valid bitcoin address' % address
        assert is_valid_btc_address(address), msg

        BaseAddressFromCredential.objects.create(
                credential=self,
                b58_address=address,
                retired_at=None)

        if set_as_merchant_address:
            self.merchant.set_destination_address(dest_address=address,
                    credential_used=self)

        return address

    def get_best_receiving_address(self, set_as_merchant_address=False):
        " Get a new receiving address "
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
