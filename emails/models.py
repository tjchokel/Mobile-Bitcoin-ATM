from django.db import models
from jsonfield import JSONField


class SentEmail(models.Model):

    POSTMARK = 'PMK'
    SENDGRID = 'SGD'

    SENDING_CHOICES = (
            (POSTMARK, 'Postmark'),
            (SENDGRID, 'Sendgrid'),
    )

    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    from_email = models.EmailField(max_length=256, null=False, blank=False,
            db_index=True)
    from_name = models.CharField(max_length=256, null=True, blank=True,
            db_index=True)
    to_email = models.EmailField(max_length=256, null=False, blank=False,
            db_index=True)
    to_name = models.CharField(max_length=256, null=True, blank=True,
            db_index=True)
    to_merchant = models.ForeignKey('merchants.Merchant', null=True, blank=True)
    cc_email = models.EmailField(max_length=256, null=True, blank=True,
            db_index=True)
    cc_name = models.CharField(max_length=256, null=True, blank=True,
            db_index=True)
    body_template = models.CharField(max_length=256, null=False, db_index=True)
    body_context = JSONField()
    subject = models.CharField(max_length=512, null=False, blank=False)
    # optional FK:
    btc_transaction = models.ForeignKey('bitcoins.BTCTransaction', null=True, blank=True)
    # TODO: data migrate and make this required
    sent_via = models.CharField(choices=SENDING_CHOICES, max_length=3, null=True, blank=True, db_index=True)

    def __str__(self):
        return '%s to %s' % (self.id, self.to_email)
