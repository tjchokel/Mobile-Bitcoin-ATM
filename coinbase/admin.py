from django.contrib import admin
from coinbase.models import APICredential, SellOrder, CurrentBalance, SendBTC


class APICredentialAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'merchant', 'api_key', 'api_secret', 'disabled_at', )
    raw_id_fields = ('merchant', )

    class Meta:
        model = APICredential

admin.site.register(APICredential, APICredentialAdmin)


class SellOrderAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'api_credential',
            'btc_transaction',
            'cb_code',
            'received_at',
            'satoshis',
            'currency_code',
            'fees_in_fiat',
            'to_receive_in_fiat',
            )
    raw_id_fields = ('api_credential', 'btc_transaction')

    class Meta:
        model = SellOrder

admin.site.register(SellOrder, SellOrderAdmin)


class CurrentBalanceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'api_credential', 'satoshis', )
    raw_id_fields = ('api_credential', )

    class Meta:
        model = CurrentBalance

admin.site.register(CurrentBalance, CurrentBalanceAdmin)


class SendBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'api_credential',
            'received_at',
            'txn_hash',
            'satoshis',
            'destination_address',
            'cb_id',
            'notes',
            )
    raw_id_fields = ('api_credential', )

    class Meta:
        model = SendBTC

admin.site.register(SendBTC, SendBTCAdmin)
