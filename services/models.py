from django.db import models

from jsonfield import JSONField

from utils import get_client_ip

import json


class APICall(models.Model):
    """
    To keep track of all our external API calls and aid in debugging as well.

    TODO: deal with security implications with data being passed in here
    """

    # api_name choices
    BCI_RECEIVE_PAYMENTS = 'BRP'
    BLOCKCYPHER_ADDR_MONITORING = 'BAM'
    BCI_TXN_FROM_HASH = 'BTH'
    BCI_TXN_FROM_ADDR = 'BTA'

    COINBASE_BALANCE = 'CBL'
    COINBASE_LIST_PURCHASE_SALE = 'CLC'
    COINBASE_LIST_BTC_TRANSACTIONS = 'CLB'
    COINBASE_SEND_BTC = 'CSB'
    COINBASE_CASHOUT_BTC = 'CSO'
    COINBASE_NEW_ADDRESS = 'CNA'

    BITSTAMP_BALANCE = 'BSB'
    BITSTAMP_LIST_TRANSACTIONS = 'BSL'
    BITSTAMP_SEND_BTC = 'BSS'
    BITSTAMP_WITHDRAWALS = 'BSW'
    BITSTAMP_BTC_ADDRESS = 'BSA'

    BLOCKCHAIN_WALLET_BALANCE = 'BWB'
    BLOCKCHAIN_WALLET_SEND_BTC = 'BWS'
    BLOCKCHAIN_WALLET_NEW_ADDRESS = 'BWN'

    API_NAME_CHOICES = (
            (BCI_RECEIVE_PAYMENTS, 'blockchain.info receive payments API'),
            (BCI_TXN_FROM_HASH, 'blockchain.info txn data from hash'),
            (BCI_TXN_FROM_ADDR, 'blockchain.info txn data from address'),
            (BLOCKCYPHER_ADDR_MONITORING, 'blockcypher address monitoring'),
            (COINBASE_BALANCE, 'Coinbase Balance'),
            (COINBASE_LIST_PURCHASE_SALE, 'Coinbase List Purchase & Sales'),
            (COINBASE_LIST_BTC_TRANSACTIONS, 'Coinbase List BTC Transactions'),
            (COINBASE_SEND_BTC, 'Coinbase Send BTC'),
            (COINBASE_CASHOUT_BTC, 'Coinbase Cashout BTC'),
            (COINBASE_NEW_ADDRESS, 'Coinbase New Address'),
            (BITSTAMP_BALANCE, 'Bitstamp Balance'),
            (BITSTAMP_LIST_TRANSACTIONS, 'Bitstamp List Transactions'),
            (BITSTAMP_SEND_BTC, 'Bitstamp Send BTC'),
            (BITSTAMP_WITHDRAWALS, 'Bitstamp Withdrawals'),
            (BITSTAMP_BTC_ADDRESS, 'Bitstamp BTC Address'),
            (BLOCKCHAIN_WALLET_BALANCE, 'Blockchain Wallet Balance'),
            (BLOCKCHAIN_WALLET_SEND_BTC, 'Blockchain Wallet Send BTC'),
            (BLOCKCHAIN_WALLET_NEW_ADDRESS, 'Blockchain Wallet New BTC Address'),
            )

    # Main fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    api_name = models.CharField(choices=API_NAME_CHOICES, max_length=3,
            null=False, blank=False, db_index=True)
    url_hit = models.URLField(blank=False, null=False, db_index=True)
    response_code = models.PositiveSmallIntegerField(blank=False, null=False,
            db_index=True)
    post_params = JSONField(blank=True, null=True)
    headers = models.CharField(max_length=2048, null=True, blank=True)
    api_results = models.CharField(max_length=100000, blank=True, null=True)

    # optional FK
    merchant = models.ForeignKey('merchants.Merchant', null=True, blank=True)


class WebHook(models.Model):
    """
    To keep track of all our webhooks and aid in debugging as well.

    TODO: deal with security implications with data being passed in here
    """

    # api_name choices
    BCI_PAYMENT_FORWARDED = 'BPF'
    BLOCKCYPHER_ADDR_MONITORING = 'BAM'
    API_NAME_CHOICES = (
            (BCI_PAYMENT_FORWARDED, 'blockchain.info payment forwarded'),
            (BLOCKCYPHER_ADDR_MONITORING, 'blockcypher address monitoring'),
            )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # IP and UA of machine hitting coinsafe
    ip_address = models.IPAddressField(null=False, blank=False, db_index=True)
    user_agent = models.CharField(max_length=1024, blank=True, db_index=True)
    api_name = models.CharField(choices=API_NAME_CHOICES, max_length=3,
            null=False, blank=False, db_index=True)
    hostname = models.CharField(max_length=512, blank=False, null=False, db_index=True)
    request_path = models.CharField(max_length=2048, blank=False, null=False, db_index=True)
    uses_https = models.BooleanField(db_index=True)
    data_from_get = JSONField(blank=True, null=True)
    data_from_post = JSONField(blank=True, null=True)

    def __str__(self):
        return '%s from %s' % (self.id, self.api_name)

    @classmethod
    def log_webhook(cls, request, api_name):
        try:
            data_from_post = json.loads(request.body)
        except Exception:
            # TODO: better edge case handling
            data_from_post = None
        return WebHook.objects.create(
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                api_name=api_name,
                hostname=request.get_host(),
                request_path=request.path,
                uses_https=request.is_secure(),
                data_from_get=request.GET,
                data_from_post=data_from_post,
                )
