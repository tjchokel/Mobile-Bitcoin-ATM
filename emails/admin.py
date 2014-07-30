from django.contrib import admin
from emails.models import SentEmail


class SentEmailAdmin(admin.ModelAdmin):
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
            'subject'
            )
    raw_id_fields = ('to_merchant', )

    class Meta:
        model = SentEmail
admin.site.register(SentEmail, SentEmailAdmin)
