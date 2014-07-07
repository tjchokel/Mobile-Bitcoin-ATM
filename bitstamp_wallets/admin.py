from django.contrib import admin

from bitstamp_wallets.models import BTSCredential, BTSSentBTC


class BTSCredentialAdmin(admin.ModelAdmin):

    list_display = ('id', 'customer_id', 'api_key', )

    class Meta:
        model = BTSCredential

admin.site.register(BTSCredential, BTSCredentialAdmin)


class BTSSentBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential',
            'txn_hash',
            'satoshis',
            'destination_btc_address',
            'destination_email',
            'withdrawal_id',
            'status',
            'status_last_checked_at',
            )

    class Meta:
        model = BTSSentBTC

admin.site.register(BTSSentBTC, BTSSentBTCAdmin)
