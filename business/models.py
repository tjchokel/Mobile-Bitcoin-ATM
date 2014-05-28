from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

from phonenumber_field.modelfields import PhoneNumberField
from bitcoins.models import BTCAddress
from countries import BFHCurrenciesList


class AppUser(AbstractUser):
    full_name = models.CharField(max_length=60, blank=True,
            null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    phone_num_country = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)

    def get_business(self):
        return self.business_set.last()

    def get_registration_step(self):
        step = 0
        business = self.get_business()
        if self.full_name:
            step += 1
        if business:
            step += 1
            if business.btc_storage_address:
                step += 1
        return step


class Business(models.Model):
    app_user = models.ForeignKey(AppUser, blank=True, null=True)
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
    btc_storage_address = models.CharField(blank=True, null=True, max_length=34,
            db_index=True)

    # TODO: Make this actually work
    def get_next_address(self):
        address = BTCAddress.objects.create(
            generated_at=now(),
            b58_address='1FXK3Qeu6ouf2haDXUCttWRHH4SLdRoFhA',
            business=self,
        )
        return address

    def get_current_address(self):
        return self.btcaddress_set.last()

    def get_all_addresses(self):
        return self.btcaddress_set.all()

    def get_all_transactions(self):
        transactions = []
        for address in self.get_all_addresses():
            transactions += address.get_all_transactions()
        return transactions

    def get_percent_markup(self):
        return self.basis_points_markup / 100.00

    def get_currency_symbol(self):
        if self.currency_code:
            return BFHCurrenciesList[self.currency_code]['symbol']
        else:
            return '$'
