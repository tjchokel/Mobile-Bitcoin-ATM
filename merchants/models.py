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

        return percent_complete

    def finished_registration(self):
        return self.get_registration_percent_complete() == 100

    def has_coinbase_credentials(self):
        return bool(self.get_coinbase_credentials())

    def has_valid_coinbase_credentials(self):
        credentials = self.get_coinbase_credentials()
        if credentials and not credentials.last_failed_at:
            return True
        else:
            return False

    def get_coinbase_credentials(self):
        return self.cbcredential_set.filter(disabled_at__isnull=True).last()

    def get_bitstamp_credentials(self):
        return self.bscredential_set.filter(disabled_at=None).last()

    def has_bitstamp_credentials(self):
        return bool(self.get_bitstamp_credentials())

    def has_valid_bitstamp_credentials(self):
        credentials = self.get_bitstamp_credentials()
        if credentials and not credentials.last_failed_at:
            return True
        return False

    def get_hours(self):
        return self.opentime_set.all()

    def get_hours_formatted(self):
        open_times = self.get_hours()
        hours_formatted = {}
        for open_time in open_times:
            hours_formatted[open_time.weekday] = {
                    'from_time': open_time.from_time,
                    'to_time': open_time.to_time,
                    }
        return hours_formatted

    def set_hours(self, hours):
        """
        hours is a list that looks like the following:
          hours = (
            (weekday, from_hour, to_hour),
            (1, datetime.time(9), datetime.time(17)),
            (2, datetime.time(9), datetime.time(17)),
          )
        """
        # Delete current hours
        self.get_hours().delete()

        # Set new hours
        for weekday, from_time, to_time in hours:
            OpenTime.objects.create(merchant=self, weekday=weekday, from_time=from_time, to_time=to_time)

    def get_website(self):
        websites = self.merchantwebsite_set.filter(deleted_at=None)
        if websites:
            return websites[0]
        return None

    def set_website(self, website_to_set):
        current_website_obj = self.get_website()
        if current_website_obj:
            if current_website_obj.url != website_to_set:
                # Mark current websites as deleted
                current_website_obj.deleted_at = now()
                current_website_obj.save()

                if website_to_set:
                    # Create (set) new website
                    MerchantWebsite.objects.create(merchant=self, url=website_to_set)
        else:
            if website_to_set:
                # Create (set) new website
                MerchantWebsite.objects.create(merchant=self, url=website_to_set)


class OpenTime(models.Model):
    # http://stackoverflow.com/a/12217171/1754586
    WEEKDAYS = (
        (1, _('Monday')),
        (2, _('Tuesday')),
        (3, _('Wednesday')),
        (4, _('Thursday')),
        (5, _('Friday')),
        (6, _('Saturday')),
        (7, _('Sunday')),
    )
    merchant = models.ForeignKey(Merchant, blank=False, null=False)

    weekday = models.IntegerField(choices=WEEKDAYS, db_index=True,
            null=False, blank=False, unique=True)
    from_time = models.TimeField()
    to_time = models.TimeField()


class MerchantWebsite(models.Model):
    # Allow multiple websites for future-proofing
    merchant = models.ForeignKey(Merchant)
    url = models.URLField(blank=False, null=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
