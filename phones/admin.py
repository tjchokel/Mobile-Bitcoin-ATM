from django.contrib import admin

from phones.models import SentSMS


class SentSMSAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'sent_at', 'phone_num', 'to_user', 'to_merchant', 'to_shopper',
    )
    raw_id_fields = ('to_user', 'to_merchant', 'to_shopper', )

    class Meta:
        model = SentSMS

admin.site.register(SentSMS, SentSMSAdmin)
