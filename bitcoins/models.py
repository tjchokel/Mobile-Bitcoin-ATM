from django.db import models
from django.core.urlresolvers import reverse

from bitcoins.bci import set_bci_webhook
from bitcoins.blockcypher import set_blockcypher_webhook
from countries import BFHCurrenciesList

from bitcash.settings import BASE_URL

from utils import uri_to_url, simple_random_generator, SATOSHIS_PER_BTC, satoshis_to_mbtc, format_mbtc

import json
import requests
import math


class DestinationAddress(models.Model):
    """
    What's uploaded by the user.
    """
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    b58_address = models.CharField(blank=False, null=False, max_length=34, db_index=True)
    retired_at = models.DateTimeField(blank=True, null=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)

    def __str__(self):
        return '%s: %s' % (self.id, self.b58_address)

    def create_new_forwarding_address(self):

        # generate random id so that each webhook has a unqiue endpoint to hit
        # this helps solve some edge cases
        kw_to_use = {'random_id': simple_random_generator(16)}

        # blockchain.info and blockcypher callback uris
        bci_uri = reverse('process_bci_webhook', kwargs=kw_to_use)
        blockcypher_uri = reverse('process_blockcypher_webhook', kwargs=kw_to_use)

        # get address to forward to (this also signs up for webhook on destination address)
        forwarding_address = set_bci_webhook(
                dest_address=self.b58_address,
                callback_url=uri_to_url(BASE_URL, bci_uri),
                merchant=self.merchant)

        # Store it in the DB
        ForwardingAddress.objects.create(
                b58_address=forwarding_address,
                destination_address=self,
                merchant=self.merchant)

        # set webhook for forwarding address
        set_blockcypher_webhook(
                monitoring_address=forwarding_address,
                callback_url=uri_to_url(BASE_URL, blockcypher_uri),
                merchant=self.merchant)

        return forwarding_address


class ForwardingAddress(models.Model):
    """
    One-time recieving address generated by blockchain.info
    """
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    b58_address = models.CharField(blank=False, null=False, max_length=34,
            db_index=True, unique=True)
    retired_at = models.DateTimeField(blank=True, null=True, db_index=True)
    destination_address = models.ForeignKey(DestinationAddress, blank=True, null=True)

    # technically, this is redundant through DestinationAddress
    # but having it here makes for easier querying
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    user_confirmed_deposit_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.b58_address)

    def get_transaction(self):
        return self.btctransaction_set.last()

    def get_all_transactions(self):
        return self.btctransaction_set.all()

    def get_current_shopper(self):
        return self.shopper_set.last()


class BTCTransaction(models.Model):
    """
    Deposits that affect our users.

    Both ForwardingAddress (initial send) and DestinationAddress (relay) are
    tracked separately in this same model.
    """
    added_at = models.DateTimeField(auto_now_add=True, db_index=True)
    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=True, null=True, db_index=True)
    conf_num = models.PositiveSmallIntegerField(blank=True, null=True, db_index=True)
    irreversible_by = models.DateTimeField(blank=True, null=True, db_index=True)
    suspected_double_spend_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # only ONE of these will ever have a match (the two txns are two separate entries)
    forwarding_address = models.ForeignKey(ForwardingAddress, blank=True, null=True)
    destination_address = models.ForeignKey(DestinationAddress, blank=True, null=True)
    # This is redundant through Address models, but having it here makes easier queries
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    # TODO: add shopper here?
    # TODO: add currency (USD, EUR, etc)?
    fiat_ammount = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    currency_code_when_created = models.CharField(max_length=5, blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.txn_hash)

    def save(self, *args, **kwargs):
        """
        Set fiat_ammount when this object is first created
        http://stackoverflow.com/a/2311499/1754586
        """
        if not self.pk:
            # This only happens if the objects isn't in the database yet.
            self.currency_code_when_created = self.merchant.currency_code
            self.fiat_ammount = self.calculate_fiat_amount()
        super(BTCTransaction, self).save(*args, **kwargs)

    def calculate_fiat_amount(self):
        merchant = self.merchant
        currency_code = merchant.currency_code or 'USD'
        url = 'https://api.bitcoinaverage.com/ticker/global/'+currency_code
        r = requests.get(url)
        content = json.loads(r.content)
        fiat_btc = content['last']
        basis_points_markup = merchant.basis_points_markup
        markup_fee = fiat_btc * basis_points_markup / 10000.00
        fiat_btc = fiat_btc - markup_fee
        fiat_total = fiat_btc * (self.satoshis / float(SATOSHIS_PER_BTC))
        return math.floor(fiat_total*100)/100

    def get_status(self):
        if self.irreversible_by:
            return 'Complete'
        else:
            return '%s confirmations' % (self.conf_num)

    def get_currency_symbol(self):
        if self.currency_code_when_created:
            return BFHCurrenciesList[self.currency_code_when_created]['symbol']
        else:
            return '$'

    def format_mbtc_amount(self):
        return format_mbtc(satoshis_to_mbtc(self.satoshis))
