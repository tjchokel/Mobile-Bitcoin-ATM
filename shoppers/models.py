from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Shopper(models.Model):
    """
    Person who is going into the store to buy/sell btc
    """
    name = models.CharField(
        blank=True, null=True, max_length=34, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    btc_address = models.ForeignKey('bitcoins.BTCAddress', blank=True, null=True)