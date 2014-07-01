from django.utils.translation import ugettext as _
from django.db import models
from django.utils.timezone import now

from countries import BFH_CURRENCY_DROPDOWN


class ParentCredential(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)

    # Optional FKs
    # FIXME: only allow one of these to be set:
    cbs_credential = models.OneToOneField('coinbase_wallets.CBSCredential', blank=True, null=True)
    bci_credential = models.OneToOneField('blockhain_wallets.BCICredential', blank=True, null=True)
    bts_credential = models.OneToOneField('bitstamp_wallets.BTSCredential', blank=True, null=True)

    # v1 logging, fancier logging to come
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s for %s' % (self.id, self.merchant.business_name)

    def get_child_model(self):
        if self.cbs_credential:
            return self.cbs_credential
        elif self.bci_credential:
            return self.bci_credential
        elif self.bts_credential:
            return self.bts_credential
        raise Exception('No Credential')

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


class ParentBalance(models.Model):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    parent_credential = models.ForeignKey(ParentCredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.satoshis)


class ParentSentBTC(models.Model):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    parent_credential = models.ForeignKey(ParentCredential, blank=False, null=False)

    # Optional FKs
    # FIXME: only allow one of these to be set:
    # Note that there is no BCISentBTC because it has no use
    cbs_sent_btc = models.OneToOneField('coinbase_wallets.CBSSentBTC', blank=True, null=True)
    bts_sent_btc = models.OneToOneField('bitstamp_wallets.BTSSentBTC', blank=True, null=True)

    # standard fields
    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_btc_address = models.CharField(max_length=34, blank=True,
            null=True, db_index=True)
    destination_email = models.EmailField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_btc_address or self.destination_email)

    def get_child_model(self):
        if self.cbs_sent_btc:
            return self.cbs_sent_btc
        elif self.bci_sent_btc:
            return self.bci_sent_btc
        elif self.bts_sent_btc:
            return self.bts_sent_btc
        raise Exception('No Child Model')


class ParentSellBTC(models.Model):
    """
    When the merchant sells BTC for fiat

    Not yet implemented on the site
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    parent_credential = models.ForeignKey(ParentCredential, blank=False, null=False)

    # Optional FKs
    # FIXME: only allow one of these to be set:
    cbs_sell_btc = models.OneToOneField('coinbase_wallets.CBSSellBTC', blank=True, null=True)
    bts_sell_btc = models.OneToOneField('bitstamp_wallets.BTSSellBTC', blank=True, null=True)

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

    def get_child_model(self):
        if self.cbs_sell_btc:
            return self.cbs_sell_btc
        elif self.bts_sell_btc:
            return self.bts_sell_btc
        raise Exception('No Child Model')
