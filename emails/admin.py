from django.contrib import admin
from emails.models import SentEmail

from bitcash.custom import ReadOnlyModelAdmin


class SentEmailAdmin(ReadOnlyModelAdmin):
    list_display = (
            'id',
            'sent_at',
            'from_email',
            'from_name',
            'to_email',
            'to_name',
            'to_merchant',
            'body_template',
            'body_context',
            'subject',
            'sent_via',
            'btc_transaction',
            )
    raw_id_fields = ('to_merchant', )
    search_fields = ['to_name', ]
    list_filter = ('sent_via', 'body_template', )

    class Meta:
        model = SentEmail
admin.site.register(SentEmail, SentEmailAdmin)
