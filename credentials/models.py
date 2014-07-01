from django.utils.translation import ugettext as _
from django.db import models
from django.utils.timezone import now

from polymorphic import PolymorphicModel

from countries import BFH_CURRENCY_DROPDOWN


class CredentialLink(models.Model):
    """ Join table to link an object to a related child credential """

    # FIXME: only allow one of these to be set:
    cbs_credential = models.OneToOneField('coinbase_wallets.CBSCredential', blank=True, null=True)
    bts_credential = models.OneToOneField('bitstamp_wallets.BTSCredential', blank=True, null=True)
    bci_credential = models.OneToOneField('blockhain_wallets.BCICredential', blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.get_credential().id)

    def get_credential(self):
        if self.cbs_credential:
            return self.cbs_credential
        elif self.bci_credential:
            return self.bci_credential
        elif self.bts_credential:
            return self.bts_credential
        raise Exception('No Credential')


class BaseCredential(PolymorphicModel):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)

    # v1 logging, fancier logging to come
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s for %s' % (self.id, self.merchant.business_name)

    def mark_success(self):
        self.last_failed_at = None
        self.last_succeded_at = now()
        return self.save()

    def mark_failure(self):
        self.last_failed_at = now()
        return self.save()

    def handle_status_code(self, status_code):
        status_code_str = str(status_code)
        if len(status_code_str.strip()) == 3 and status_code_str.startswith('2'):
            self.mark_success()
        else:
            self.mark_failure
            err_msg = 'Expected 2xx but got %s' % status_code
            raise Exception('StatusCode: %s' % err_msg)

    def get_status(self):
        if self.last_failed_at:
            return _('Invalid')
        else:
            return _('Valid')


class BaseBalance(PolymorphicModel):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential_link = models.ForeignKey(CredentialLink, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.satoshis)

    def get_credential(self):
        return self.credential_link.get_credential()


class BaseSentBTC(PolymorphicModel):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential_link = models.ForeignKey(CredentialLink, blank=False, null=False)

    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_btc_address = models.CharField(max_length=34, blank=True,
            null=True, db_index=True)
    destination_email = models.EmailField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_btc_address or self.destination_email)

    def get_credential(self):
        return self.credential_link.get_credential()


class BaseSellBTC(PolymorphicModel):
    """
    When the merchant sells BTC for fiat

    Not yet implemented on the site
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential_link = models.ForeignKey(CredentialLink, blank=False, null=False)

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

    def get_credential(self):
        return self.credential_link.get_credential()
