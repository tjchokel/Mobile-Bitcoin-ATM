from django.db import models

from phonenumber_field.modelfields import PhoneNumberField

from phones.plivo_sms import send_sms


class SentSMS(models.Model):
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    phone_num = PhoneNumberField(blank=False, null=False, db_index=True)
    message = models.CharField(max_length=1024, null=False, blank=False)
    to_user = models.ForeignKey('users.AuthUser', null=True, blank=True)
    to_merchant = models.ForeignKey('merchants.Merchant', null=True, blank=True)
    to_shopper = models.ForeignKey('shoppers.Shopper', null=True, blank=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.phone_num)

    @classmethod
    def send_and_log(self, phone_num, message, to_user, to_merchant, to_shopper):
        ''' Send message and log it '''

        # Log the msg
        sent_sms = SentSMS.objects.create(
                phone_num=phone_num,
                message=message,
                to_user=to_user,
                to_merchant=to_merchant,
                to_shopper=to_shopper)

        # Debug Message
        print 'Sending to %s: %s' % (sent_sms.phone_num.as_international, message)

        # Sent the message
        send_sms(dst=sent_sms.phone_num.as_international, text=message)

        # Return the log
        return sent_sms
