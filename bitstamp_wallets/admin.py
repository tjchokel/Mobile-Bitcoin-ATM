from django.contrib import admin

from bitstamp_wallets.models import BTSCredential, BTSSentBTC


class BTSCredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'merchant',
            'disabled_at',
            'last_succeded_at',
            'last_failed_at',
            'customer_id',
            'api_key',
            )
    raw_id_fields = ('merchant', )

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
    raw_id_fields = ('credential', )

    class Meta:
        model = BTSSentBTC

admin.site.register(BTSSentBTC, BTSSentBTCAdmin)
