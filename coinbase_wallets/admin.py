from django.contrib import admin

from coinbase_wallets.models import CBSCredential, CBSSentBTC, CBSSellBTC


class CBSCredentialAdmin(admin.ModelAdmin):

    list_display = ('id', 'api_key', )

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

    class Meta:
        model = CBSSentBTC

admin.site.register(CBSSentBTC, CBSSentBTCAdmin)


class CBSSellBTCAdmin(admin.ModelAdmin):
    list_display = ('id', 'coinbase_code', )

    class Meta:
        model = CBSSellBTC

admin.site.register(CBSSellBTC, CBSSellBTCAdmin)
