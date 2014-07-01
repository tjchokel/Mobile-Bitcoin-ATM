from django.contrib import admin

from bitstamp_wallets.models import BTSCredential, BTSSentBTC


class BTSCredentialAdmin(admin.ModelAdmin):

    list_display = ('id', 'username', 'api_key', )

    class Meta:
        model = BTSCredential

admin.site.register(BTSCredential, BTSCredentialAdmin)


class BTSSentBTCAdmin(admin.ModelAdmin):
    list_display = ('id', 'withdrawal_id', 'status', 'status_last_checked_at', )

    class Meta:
        model = BTSSentBTC

admin.site.register(BTSSentBTC, BTSSentBTCAdmin)
