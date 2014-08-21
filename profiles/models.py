from django.db import models
from django.core.urlresolvers import reverse

from utils import uri_to_url
from bitcash.settings import BASE_URL


class ShortURL(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    uri_display = models.CharField(max_length=256, blank=False, null=False, db_index=True)
    # used to enforce no collissions at the database level:
    uri_lowercase = models.CharField(max_length=256, blank=False, null=False, unique=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    deleted_at = models.DateTimeField(db_index=True, blank=True, null=True)

    def __str__(self):
        return '%s (%s) for %s' % (self.id, self.uri_lowercase, self.merchant.business_name)

    def save(self, *args, **kwargs):
        """
        Enforce uri_display and uri_lowercase logic
        """
        self.uri_lowercase = self.uri_display.lower()
        super(ShortURL, self).save(*args, **kwargs)

    def get_admin_uri(self):
        return reverse('admin:profiles_shorturl_change', args=(self.id, ))

    def get_new_admin_uri(self):
        return reverse('admin:profiles_shorturl_add')

    def get_profile_uri(self):
        return reverse('merchant_site', kwargs={'uri': self.uri_display})

    def get_profile_url(self):
        return uri_to_url(BASE_URL, self.uri_display)


class MerchantDoc(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    img_file = models.FileField(upload_to='store-img/%Y%m%d/%H%M%S-%s', blank=False, null=False)

    def __str__(self):
        return '%s for %s' % (self.id, self.merchant)

    def get_url(self):
        " Returns the url to show to use in templates "
        # TODO: make this an unsigned URL (for browser caching)
        return self.img_file.url
