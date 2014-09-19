from django.contrib import admin

from phones.models import SentSMS

from bitcash.custom import ReadOnlyModelAdmin


class SentSMSAdmin(ReadOnlyModelAdmin):
    list_display = (
        'id', 'sent_at', 'phone_num', 'to_user', 'to_merchant', 'to_shopper',
    )
    raw_id_fields = ('to_user', 'to_merchant', 'to_shopper', )

    class Meta:
        model = SentSMS

admin.site.register(SentSMS, SentSMSAdmin)
