from django.db import models
from jsonfield import JSONField


class SentEmail(models.Model):
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

    def __str__(self):
        return '%s' % self.id
