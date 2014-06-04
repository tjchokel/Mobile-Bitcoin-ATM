from django.db import models
from django.utils.timezone import now

from phonenumber_field.modelfields import PhoneNumberField
from bitcoins.models import DestinationAddress

from countries import BFHCurrenciesList


class Merchant(models.Model):
    user = models.ForeignKey('users.CashUser', blank=True, null=True)
    business_name = models.CharField(
        max_length=256, blank=False, null=False, db_index=True)
    address_1 = models.CharField(
        max_length=256, blank=False, null=False, db_index=True)
    address_2 = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)
    city = models.CharField(
        max_length=256, blank=False, null=False, db_index=True)
    state = models.CharField(max_length=30, null=True, blank=True, db_index=True)
    country = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)
    zip_code = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    hours = models.CharField(
        max_length=256, blank=False, null=False, db_index=True)
    currency_code = models.CharField(
        max_length=5, blank=True, null=True, db_index=True)
    basis_points_markup = models.IntegerField(blank=True, null=True, db_index=True, default=100)

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
        return bool(self.get_destination_address)

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

    def get_all_transactions(self):
        return self.btctransaction_set.all()

    def get_percent_markup(self):
        return self.basis_points_markup / 100.00

    def get_currency_symbol(self):
        if self.currency_code:
            return BFHCurrenciesList[self.currency_code]['symbol']
        else:
            return '$'

    def get_currency_name(self):
        if self.currency_code:
            return BFHCurrenciesList[self.currency_code]['label']
        else:
            return 'United States dollar'
