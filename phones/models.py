from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from phones.plivo_sms import send_sms


class SentSMS(models.Model):

    MERCHANT_TX_CONFIRMED = 'MTC'
    MERCHANT_NEW_TX = 'MNT'
    SHOPPER_TX_CONFIRMED = 'STC'
    SHOPPER_NEW_TX = 'SNT'
    UNKNOWN = 'NA'  # used for intial legacy migration
    MSG_TYPE_CHOICES = (
            (MERCHANT_TX_CONFIRMED, 'Merchant Transaction Confirmed'),
            (MERCHANT_NEW_TX, 'Merchant New Transaction'),
            (SHOPPER_TX_CONFIRMED, 'Shopper Transaction Confirmed'),
            (SHOPPER_NEW_TX, 'Shopper New Transaction'),
            )

    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    phone_num = PhoneNumberField(blank=False, null=False, db_index=True)
    message = models.CharField(max_length=1024, null=False, blank=False)
    to_user = models.ForeignKey('users.AuthUser', null=True, blank=True)
    to_merchant = models.ForeignKey('merchants.Merchant', null=True, blank=True)
    to_shopper = models.ForeignKey('shoppers.Shopper', null=True, blank=True)
    message_type = models.CharField(choices=MSG_TYPE_CHOICES, max_length=3,
            null=False, blank=False, db_index=True)
    # optional FK:
    btc_transaction = models.ForeignKey('bitcoins.BTCTransaction', null=True, blank=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.phone_num)

    @classmethod
    def send_and_log(cls, phone_num, message, to_user, to_merchant, to_shopper, btc_transaction):
        ''' Send message and log it '''

        # Log the msg
        sent_sms = cls.objects.create(
                phone_num=phone_num,
                message=message,
                to_user=to_user,
                to_merchant=to_merchant,
                to_shopper=to_shopper,
                btc_transaction=btc_transaction,
                )

        # Sent the message
        send_sms(dst=sent_sms.phone_num.as_international, text=message)

        # Return the log
        return sent_sms
