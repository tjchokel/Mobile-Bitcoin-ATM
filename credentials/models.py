from django.utils.translation import ugettext as _
from django.db import models
from django_fields.fields import EncryptedCharField

from countries import BFH_CURRENCY_DROPDOWN


class Credential(models.Model):

    COINBASE = 'CBS'
    BITSTAMP = 'BTS'
    BLOCKCHAIN_INFO = 'BCI'

    CREDENTIAL_TYPES = (
            (COINBASE, 'CoinBase'),
            (BITSTAMP, 'BitStamp'),
            (BLOCKCHAIN_INFO, 'blockchain.info'),
            )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential_type = models.CharField(choices=CREDENTIAL_TYPES, max_length=3,
            null=False, blank=False, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    # Both of these are extra-long for safety
    api_key = EncryptedCharField(max_length=128, blank=False, null=False, db_index=True)
    api_secret = EncryptedCharField(max_length=256, blank=False, null=False, db_index=True)
    secondary_secret = EncryptedCharField(max_length=256, blank=True, null=True, db_index=True)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # v1 logging, fancier logging to come
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s for %s from %s' % (self.id,
                self.get_credential_type_display(),
                self.merchant.business_name)

    def get_status(self):
        if self.last_failed_at:
            return _('Invalid')
        else:
            return _('Valid')

    def get_custom_methods(self):
        """
        Get a custom object that is very django model-like with all the methods

        Kind of a hack, is there a better way to do this?
        """
        if self.credential_type == 'CBS':
            from credentials.coinbase_api import CBSCredential
            return CBSCredential(self)
        elif self.credential_type == 'BTS':
            from credentials.bitstamp_api import BTSCredential
            return BTSCredential(self)
        elif self.credential_type == 'BCI':
            from credentials.blockchain_api import BCICredential
            return BCICredential(self)
        else:
            raise Exception('Credential Type Not Implemented: %s' % self.credential_type)


class CurrentBalance(models.Model):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(Credential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.satoshis)


class SentBTC(models.Model):

    BS_STATUS_CHOICES = (
        ('0', 'Open'),
        ('1', 'In Process'),
        ('2', 'Finished'),
        ('3', 'Canceled'),
        ('4', 'Failed'),
        )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(Credential, blank=False, null=False)
    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_btc_address = models.CharField(max_length=34, blank=True,
            null=True, db_index=True)
    destination_email = models.EmailField(blank=True, null=True, db_index=True)
    unique_id = models.CharField(max_length=64, blank=False, null=False, db_index=True)
    notes = models.CharField(max_length=2048, blank=True, null=True)
    # For Bitstamp only
    status = models.CharField(choices=BS_STATUS_CHOICES, max_length=1,
            null=True, blank=True, db_index=True)
    # To use with polling (since we don't get this data on creation)
    status_last_checked_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_email or self.destination_btc_address)


class SellBTCOrder(models.Model):
    """
    When the merchant sells BTC for fiat

    Not yet implemented on the site
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(Credential, blank=False, null=False)
    custom_code = models.CharField(max_length=32, blank=False, null=False, db_index=True, unique=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    currency_code = models.CharField(max_length=5, blank=False, null=False,
            db_index=True, choices=BFH_CURRENCY_DROPDOWN)
    # Exchange and related bank fees
    fees_in_fiat = models.DecimalField(blank=True, null=True, max_digits=10,
            decimal_places=2, db_index=True)
    # what's received by user after fees
    to_receive_in_fiat = models.DecimalField(blank=False, null=False,
            max_digits=10, decimal_places=2, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.created_at)

    def get_custom_methods(self):
        """
        Get a custom object that is very django model-like with all the methods

        Kind of a hack, is there a better way to do this?
        """
        if self.credential_type == 'BTS':
            from credentials.bitstamp_api import BTSSellOrder
            return BTSSellOrder(self)
        else:
            raise Exception('NotImplemented: %s' % self.credential_type)
