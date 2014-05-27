from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now

from phonenumber_field.modelfields import PhoneNumberField
from bitcoins.models import BTCAddress


class AppUser(AbstractUser):
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)

    def get_business(self):
        return self.business_set.last()


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
    country = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)
    zip_code = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    hours = models.CharField(
        max_length=256, blank=False, null=False, db_index=True)
    currency_code = models.CharField(
        max_length=5, blank=True, null=True, db_index=True)

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