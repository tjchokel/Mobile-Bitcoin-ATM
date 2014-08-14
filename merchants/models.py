from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from annoying.functions import get_object_or_None

from coinbase_wallets.models import CBSCredential
from blockchain_wallets.models import BCICredential
from bitstamp_wallets.models import BTSCredential

from phonenumber_field.modelfields import PhoneNumberField

from bitcoins.models import DestinationAddress, ShopperBTCPurchase, BTCTransaction
from profiles.models import ShortURL

from emails.trigger import send_and_log

from utils import format_satoshis_with_units, mbtc_to_satoshis, satoshis_to_btc

from countries import BFHCurrenciesList, ALL_COUNTRIES, BFH_CURRENCY_DROPDOWN

import math
import urllib
import requests
import json


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
    cashin_markup_in_bps = models.IntegerField(blank=True, null=True, db_index=True)
    cashout_markup_in_bps = models.IntegerField(blank=True, null=True, db_index=True)
    minimum_confirmations = models.PositiveSmallIntegerField(blank=True, null=True, db_index=True, default=1)
    max_mbtc_shopper_purchase = models.IntegerField(blank=True, null=True, db_index=True, default=1000)
    max_mbtc_shopper_sale = models.IntegerField(blank=True, null=True, db_index=True, default=1000)
    longitude_position = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)
    latitude_position = models.DecimalField(max_digits=8, decimal_places=3, blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.business_name)

    def get_destination_addresses(self):
        # There should only ever be one at a time
        return self.destinationaddress_set.filter(retired_at__isnull=True)

    def get_destination_address(self):
        destination_addresses = self.get_destination_addresses()
        if destination_addresses:
            return destination_addresses[0]
        else:
            return None

    def has_destination_address(self):
        return bool(self.get_destination_address())

    def set_destination_address(self, dest_address, credential_used=None):
        matching_address = self.destinationaddress_set.filter(
                b58_address=dest_address,
                credential=credential_used,
                retired_at=None)
        if matching_address:
            # Should only have one, but still is a queryset
            return matching_address[0]
        else:
            # Mark all current active destination addresses as retired
            for dest_addr in DestinationAddress.objects.filter(merchant=self, retired_at=None):
                dest_addr.retired_at = now()
                dest_addr.save()

            # Create new address object
            return DestinationAddress.objects.create(
                    b58_address=dest_address,
                    merchant=self,
                    credential=credential_used)

    def get_phone_num_formatted(self):
        if self.phone_num:
            return self.phone_num.as_international
        return None

    def set_new_forwarding_address(self):
        return self.get_destination_address().create_new_forwarding_address()

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
        cash_in_txns = ShopperBTCPurchase.objects.active(merchant=self)

        combined_transactions = [w for w in cash_in_txns]
        combined_transactions.extend(cash_out_txns)

        combined_transactions = sorted(combined_transactions, key=lambda x: x.added_at, reverse=True)
        return combined_transactions

    def get_bitcoin_purchase_request(self):
        return self.shopperbtcpurchase_set.filter(cancelled_at__isnull=True,
            confirmed_by_merchant_at__isnull=True).last()

    def get_percent_markup(self):
        return self.basis_points_markup / 100.00

    def get_cashout_percent_markup(self):
        if self.cashout_markup_in_bps:
            return self.cashout_markup_in_bps / 100.00
        else:
            return self.basis_points_markup / 100.00

    def get_cashin_percent_markup(self):
        if self.cashin_markup_in_bps:
            return self.cashin_markup_in_bps / 100.00
        else:
            return self.basis_points_markup / 100.00

    def get_currency_symbol(self):
        if self.currency_code:
            return BFHCurrenciesList[self.currency_code]['symbol'].decode('utf-8')
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
        if self.has_valid_api_credential():
            percent_complete += 10

        return percent_complete

    def finished_registration(self):
        return self.get_registration_percent_complete() == 100

    def has_valid_api_credential(self):
        cb = self.has_valid_coinbase_credentials()
        bs = self.has_valid_bitstamp_credentials()
        bci = self.has_valid_blockchain_credentials()
        return any([cb, bs, bci])

    def get_valid_api_credential(self):
        if self.has_valid_coinbase_credentials():
            return self.get_coinbase_credential()
        elif self.has_valid_bitstamp_credentials():
            return self.get_bitstamp_credential()
        elif self.has_valid_blockchain_credentials():
            return self.get_blockchain_credential()
        return None

    def has_coinbase_credentials(self):
        return bool(self.get_coinbase_credential())

    def has_valid_coinbase_credentials(self):
        credentials = self.get_coinbase_credential()
        if credentials and not credentials.last_failed_at:
            return True
        else:
            return False

    def get_coinbase_credential(self):
        return self.basecredential_set.instance_of(
                CBSCredential).filter(disabled_at=None).last()

    def get_bitstamp_credential(self):
        return self.basecredential_set.instance_of(
                BTSCredential).filter(disabled_at=None).last()

    def get_blockchain_credential(self):
        return self.basecredential_set.instance_of(
                BCICredential).filter(disabled_at=None).last()

    def has_blockchain_credentials(self):
        return bool(self.get_blockchain_credential())

    def has_valid_blockchain_credentials(self):
        credentials = self.get_blockchain_credential()
        if credentials and not credentials.last_failed_at:
            return True
        return False

    def has_bitstamp_credentials(self):
        return bool(self.get_bitstamp_credential())

    def has_valid_bitstamp_credentials(self):
        credentials = self.get_bitstamp_credential()
        if credentials and not credentials.last_failed_at:
            return True
        return False

    def disable_all_credentials(self):
        " use this when reseting a user's password "
        for credential in self.basecredential_set.filter(disabled_at=None):
            credential.disabled_at = now()
            credential.save()

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

    def get_website_obj(self):
        websites = self.merchantwebsite_set.filter(deleted_at=None)
        if websites:
            return websites[0]
        return None

    def set_website(self, website_to_set):
        current_website_obj = self.get_website_obj()
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

    def has_finished_registration(self):
        return self.has_destination_address()

    def get_max_mbtc_sale_formatted(self):
        return format_satoshis_with_units(mbtc_to_satoshis(self.max_mbtc_shopper_sale))

    def get_max_mbtc_purchase_formatted(self):
        return format_satoshis_with_units(mbtc_to_satoshis(self.max_mbtc_shopper_purchase))

    def send_welcome_email(self):
        """
        Send graphics and upsell to fill out profile (if neccesary)
        """
        body_context = {
                'profile_url': reverse('merchant_profile'),
                'promotional_material': reverse('promotional_material'),
                }
        return send_and_log(
                subject='Welcome to CoinSafe ',
                body_template='merchant/welcome_to_coinsafe.html',
                to_merchant=self,
                body_context=body_context,
                )

    def get_physical_address_list(self):
        """
        Returns a list of address strings that can be manipulated (for display, a mapping API, etc):

            ['123 Fake St', 'Apt #1', 'City, State, Country', 'USA']
        """
        location_strings = []
        if self.country:
            location_strings.append(self.country)
            if self.state and self.city and self.zip_code:
                location_strings.append('%s %s %s' % (self.city, self.state, self.zip_code))
            elif self.state and self.city:
                location_strings.append('%s %s' % (self.city, self.state))
            else:
                if self.city:
                    location_strings.append(self.city)
                if self.state:
                    location_strings.append(self.state)
            if not self.state or not self.city:
                if self.zip_code:
                    location_strings.append(self.zip_code)
            if self.address_2:
                location_strings.append(self.address_2)
            if self.address_1:
                location_strings.append(self.address_1)
        location_strings.reverse()
        return location_strings

    def get_physical_address_html(self):
        return '<br />'.join(self.get_physical_address_list())

    def get_physical_address_qs(self):
        return urllib.quote(' '.join(self.get_physical_address_list()))

    def calculate_fiat_amount(self, satoshis):
        """
        Calculates the fiat amount that X satoshis gets you right now.
        """

        fiat_btc = BTCTransaction.get_btc_market_price(self.currency_code)
        markup_fee = fiat_btc * self.get_cashout_percent_markup() / 100.00
        fiat_btc = fiat_btc - markup_fee
        fiat_total = fiat_btc * satoshis_to_btc(satoshis)
        return math.floor(fiat_total*100)/100

    def get_short_url_obj(self):
        """
        A user may have multiple short URLs, but we'll only surface one
        """
        return self.shorturl_set.order_by('created_at').last()

    def create_short_url(self, counter=1):
        """
        Dumb method to create a short url from the slugified business name.
        """
        if counter > 1:
            slug = slugify('%s %s' % (self.business_name, counter))
        else:
            slug = slugify(self.business_name)
        existing_shorturl_obj = get_object_or_None(ShortURL, uri_lowercase=slug)
        if existing_shorturl_obj:
            return self.create_short_url(counter+1)
        else:
            return ShortURL.objects.create(uri_display=slug, merchant=self)

    def set_latitude_longitude(self):
        address_array = self.get_physical_address_list()
        # address = self.get_physical_address_qs()
        # address_string = address.replace(" ", "+")
        url = "https://maps.googleapis.com/maps/api/geocode/json?address="
        for line in address_array:
            url += line.replace(" ", "+")
            url += ","
        r = requests.get(url)
        content = json.loads(r.content)
        results = content['results']

        if results:
            latitude = results[0]['geometry']['location']['lat']
            longitude = results[0]['geometry']['location']['lng']

            self.latitude_position = latitude
            self.longitude_position = longitude

            self.save()

    def get_profile_url(self):
        short_url = self.get_short_url_obj()
        if short_url:
            return short_url.get_profile_url()
        else:
            return None

    def get_open_time(self):
        return self.opentime_set.last()


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

    def __str__(self):
        return '%s: %s from %s to %s' % (self.id, self.weekday,
                self.from_time, self.to_time)


class MerchantWebsite(models.Model):
    # Allow multiple websites for future-proofing
    merchant = models.ForeignKey(Merchant)
    url = models.URLField(blank=False, null=False, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.url)
