from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Shopper(models.Model):
    """
    Person who is going into the store to buy/sell btc
    """
    name = models.CharField(blank=True, null=True, max_length=34, db_index=True)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.name)

    def get_notification_methods_formatted(self):
        if self.email and self.phone_num:
            return 'email and phone'
        elif self.email:
            return 'email'
        elif self.phone:
            return 'phone'
        else:
            return ''

    def get_transaction_table_string(self):
        if self.name:
            return self.name
        else:
            return self.email
