from django.contrib import admin

from coinbase_wallets.models import CBSCredential, CBSSentBTC, CBSSellBTC


class CBSCredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'merchant',
            'disabled_at',
            'last_succeded_at',
            'last_failed_at',
            'api_key',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = CBSCredential

admin.site.register(CBSCredential, CBSCredentialAdmin)


class CBSSentBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential',
            'txn_hash',
            'satoshis',
            'destination_btc_address',
            'destination_email',
            'transaction_id',
            'notes',
            )
    raw_id_fields = ('credential', )

    class Meta:
        model = CBSSentBTC

admin.site.register(CBSSentBTC, CBSSentBTCAdmin)


class CBSSellBTCAdmin(admin.ModelAdmin):
    list_display = ('id', 'coinbase_code', )
    raw_id_fields = ('credential', )

    class Meta:
        model = CBSSellBTC

admin.site.register(CBSSellBTC, CBSSellBTCAdmin)
