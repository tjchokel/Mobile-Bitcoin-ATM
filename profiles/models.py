from django.db import models


class ShortURL(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # only allow lowercase to be saved into the database to avoid collisions:
    uri = models.CharField(max_length=256, blank=False, null=False, unique=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    deleted_at = models.DateTimeField(db_index=True, blank=True, null=True)

    def __str__(self):
        return '%s for %s' % (self.id, self.merchant)
