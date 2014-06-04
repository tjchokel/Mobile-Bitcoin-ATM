from django.db import models
from django.contrib.auth.models import AbstractUser

from phonenumber_field.modelfields import PhoneNumberField


class CashUser(AbstractUser):
    """
    Right now this is just merchants but it can support cashiers, shoppers,
    owners with multiple merchants and all types of things in the future.

    http://qr.ae/svQjw
    """
    full_name = models.CharField(max_length=60, blank=True,
            null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    phone_num_country = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)

    def get_merchant(self):
        return self.merchant_set.last()

    def get_registration_step(self):
        step = 0
        merchant = self.get_merchant()
        if self.full_name:
            step += 1
        if merchant:
            step += 1
            if merchant.has_destination_address():
                step += 1
        return step
