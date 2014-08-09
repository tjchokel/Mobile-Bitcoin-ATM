from django.contrib import admin
from profiles.models import ShortURL

from utils import uri_to_url

from bitcash.settings import BASE_URL


class ShortURLAdmin(admin.ModelAdmin):

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
