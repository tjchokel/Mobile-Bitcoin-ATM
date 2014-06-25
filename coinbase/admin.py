from django.contrib import admin
from coinbase.models import CBCredential, SellOrder, CurrentBalance, SendBTC


class CBCredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'merchant',
            'last_succeded_at',
            'last_failed_at',
            'disabled_at',
            'api_key',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = CBCredential

admin.site.register(CBCredential, CBCredentialAdmin)


class SellOrderAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'cb_credential',
            'btc_transaction',
            'cb_code',
            'received_at',
            'satoshis',
            'currency_code',
            'fees_in_fiat',
            'to_receive_in_fiat',
            )
    raw_id_fields = ('cb_credential', 'btc_transaction')

    class Meta:
        model = SellOrder

admin.site.register(SellOrder, SellOrderAdmin)


class CurrentBalanceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'cb_credential', 'satoshis', )
    raw_id_fields = ('cb_credential', )

    class Meta:
        model = CurrentBalance

admin.site.register(CurrentBalance, CurrentBalanceAdmin)


class SendBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'cb_credential',
            'received_at',
            'txn_hash',
            'satoshis',
            'destination_btc_address',
            'destination_email',
            'cb_id',
            'notes',
            )
    raw_id_fields = ('cb_credential', )

    class Meta:
        model = SendBTC

admin.site.register(SendBTC, SendBTCAdmin)
