from django.contrib import admin
from profiles.models import ShortURL, MerchantDoc

from utils import uri_to_url

from bitcash.settings import BASE_URL
from bitcash.custom import ReadOnlyModelAdmin


class ShortURLAdmin(ReadOnlyModelAdmin):

    def short_url(self, instance):
        url = uri_to_url(BASE_URL, instance.uri_display)
        return '<a href="%s">%s</a>' % (url, instance.uri_display)
    short_url.allow_tags = True

    list_display = (
            'id',
            'created_at',
            'short_url',
            'merchant',
            'deleted_at',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = ShortURL

admin.site.register(ShortURL, ShortURLAdmin)


class MerchantDocAdmin(ReadOnlyModelAdmin):

    list_display = (
            'id',
            'uploaded_at',
            'deleted_at',
            'merchant',
            'img_file',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = MerchantDoc

admin.site.register(MerchantDoc, MerchantDocAdmin)
