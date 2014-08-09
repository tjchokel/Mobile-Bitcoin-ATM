from django.contrib import admin
from profiles.models import ShortURL


class ShortURLAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'created_at',
            'uri',
            'merchant',
            'deleted_at',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = ShortURL

admin.site.register(ShortURL, ShortURLAdmin)
