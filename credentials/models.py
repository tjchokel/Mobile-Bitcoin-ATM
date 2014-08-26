from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.utils.timezone import now
from django.core.urlresolvers import reverse

from bitcoins.BCAddressField import is_valid_btc_address

from polymorphic import PolymorphicModel

from countries import BFH_CURRENCY_DROPDOWN

from utils import format_satoshis_with_units


class BaseCredential(PolymorphicModel):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    disabled_at = models.DateTimeField(blank=True, null=True, db_index=True)

    # v1 logging, fancier logging to come
    last_succeded_at = models.DateTimeField(blank=True, null=True, db_index=True)
    last_failed_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s for %s' % (self.id, self.merchant.business_name)

    def get_admin_uri(self):
        # This takes you to the BaseCredential, you probably want the subclassed model
        return reverse('admin:credentials_basecredential_change', args=(self.id, ))

    def mark_success(self):
        self.last_failed_at = None
        self.last_succeded_at = now()
        return self.save()

    def mark_failure(self):
        self.last_failed_at = now()
        return self.save()

    def mark_disabled(self):
        self.disabled_at = now()
        return self.save()

    def handle_status_code(self, status_code):
        """
        Return True if status code valid, False otherwise
        """
        status_code_str = str(status_code)
        if len(status_code_str.strip()) == 3 and status_code_str.startswith('2'):
            self.mark_success()
            return True
        else:
            self.mark_failure()
            return False

    def get_credential_abbrev(self):
        raise Exception('Not Implemented')

    def get_credential_to_display(self):
        raise Exception('Not Implemented')

    def get_login_link(self):
        raise Exception('Not Implemented')

    def get_status(self):
        if self.last_failed_at:
            return _('Invalid')
        else:
            return _('Valid')


class BaseBalance(PolymorphicModel):
    """ Probably just used as a log and not implemented anywhere """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(BaseCredential, blank=False, null=False)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, format_satoshis_with_units(self.satoshis))


class BaseSentBTC(PolymorphicModel):

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(BaseCredential, blank=False, null=False)

    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=False, null=False, db_index=True)
    destination_btc_address = models.CharField(max_length=34, blank=True,
            null=True, db_index=True)
    destination_email = models.EmailField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.destination_btc_address or self.destination_email)


class BaseAddressFromCredential(PolymorphicModel):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(BaseCredential, blank=False, null=False)
    b58_address = models.CharField(blank=False, null=False, max_length=34, db_index=True)
    retired_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.b58_address)

    def save(self, *args, **kwargs):
        """
        Be sure b58_address is valid before saving
        """
        assert is_valid_btc_address(self.b58_address), self.b58_address

        super(BaseAddressFromCredential, self).save(*args, **kwargs)


class BaseSellBTC(PolymorphicModel):
    """
    When the merchant sells BTC for fiat

    Not yet implemented on the site
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    credential = models.ForeignKey(BaseCredential, blank=False, null=False)

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
