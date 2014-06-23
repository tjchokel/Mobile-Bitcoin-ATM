from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from phonenumber_field.modelfields import PhoneNumberField
from bitcoins.models import DestinationAddress

from countries import BFHCurrenciesList, ALL_COUNTRIES, BFH_CURRENCY_DROPDOWN


class Merchant(models.Model):
    user = models.ForeignKey('users.AuthUser', blank=True, null=True)
    business_name = models.CharField(max_length=256, blank=False, null=False, db_index=True)
    address_1 = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    address_2 = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    city = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    state = models.CharField(max_length=30, null=True, blank=True, db_index=True)
    country = models.CharField(max_length=256, blank=True, null=True, db_index=True, choices=ALL_COUNTRIES)
    zip_code = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    hours = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    currency_code = models.CharField(max_length=5, blank=False, null=False, db_index=True, choices=BFH_CURRENCY_DROPDOWN)
    basis_points_markup = models.IntegerField(blank=True, null=True, db_index=True, default=100)
    minimum_confirmations = models.PositiveSmallIntegerField(blank=True, null=True, db_index=True, default=1)

    def get_new_forwarding_address(self):
        return self.get_destination_address().create_new_forwarding_address()

    def get_active_dest_addresses(self):
        # There should only ever be one at a time
        return self.destinationaddress_set.filter(retired_at__isnull=True)

    def get_destination_address(self):
        destination_addresses = self.get_active_dest_addresses()
        if destination_addresses:
            return destination_addresses[0]
        return None

    def __str__(self):
        return '%s: %s' % (self.id, self.business_name)

    def has_destination_address(self):
        return bool(self.get_destination_address())

    def set_destination_address(self, dest_address):
        matching_address = self.destinationaddress_set.filter(b58_address=dest_address)
        if matching_address:
            # Should only have one, but still is a queryset
            for address in matching_address:
                if address.retired_at:
                    address.retired_at = None
                    address.save()
        else:
            # Mark all other addresses retired
            for active_address in self.get_active_dest_addresses():
                active_address.retired_at = now()
                active_address.save()
            # Create new address object
            DestinationAddress.objects.create(b58_address=dest_address, merchant=self)

    def get_all_forwarding_addresses(self):
        return self.forwardingaddress_set.all()

    def get_all_forwarding_transactions(self):
        txns = []
        for forwarding_addr in self.forwardingaddress_set.order_by('-id'):
            txns.extend(forwarding_addr.btctransaction_set.filter(destination_address__isnull=True).order_by('-id'))
        return txns

    def get_combined_transactions(self):
        """
            Get's all transactions for cash in and cash out

            Sorts by added_at
        """
        cash_out_txns = self.get_all_forwarding_transactions()
        cash_in_txns = self.shopperbtcpurchase_set.filter(cancelled_at__isnull=True).all()

        combined_transactions = [w for w in cash_in_txns]
        combined_transactions.extend(cash_out_txns)

        combined_transactions = sorted(combined_transactions, key=lambda x: x.added_at, reverse=True)
        return combined_transactions

    def get_bitcoin_purchase_request(self):
        return self.shopperbtcpurchase_set.filter(cancelled_at__isnull=True, confirmed_by_merchant_at__isnull=True).last()

    def get_percent_markup(self):
        return self.basis_points_markup / 100.00

    def get_currency_symbol(self):
        if self.currency_code:
            return BFHCurrenciesList[self.currency_code]['symbol']
        else:
            return '$'

    def get_currency_name(self):
        return BFHCurrenciesList[self.currency_code]['label']

    def get_registration_percent_complete(self):
        percent_complete = 50
        if self.address_1:
            percent_complete += 10
        if self.city:
            percent_complete += 10
        if self.state:
            percent_complete += 10
        if self.phone_num:
            percent_complete += 10
        if self.has_valid_coinbase_credentials():
            percent_complete += 10
        # if self.hours:
        #     percent_complete += 10
        return percent_complete

    def finished_registration(self):
        return self.get_registration_percent_complete() == 100

    def has_coinbase_credentials(self):
        # TODO: MAKE THIS WORK
        return len(self.cbcredential_set.filter(disabled_at__isnull=True).all()) > 0

    def has_valid_coinbase_credentials(self):
        credentials = self.get_coinbase_credentials()
        if credentials and not credentials.last_failed_at:
            return True
        else:
            return False

    def get_coinbase_credentials(self):
        # TODO: MAKE THIS WORK
        return self.cbcredential_set.filter(disabled_at__isnull=True).last()
