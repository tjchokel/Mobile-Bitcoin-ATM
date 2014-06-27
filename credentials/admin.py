from django.contrib import admin
from credentials.models import Credential, SellBTCOrder, CurrentBalance, SentBTC


class CredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential_type',
            'merchant',
            'api_key',
            'last_succeded_at',
            'last_failed_at',
            'disabled_at',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = Credential

admin.site.register(Credential, CredentialAdmin)


class CurrentBalanceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'credential', 'satoshis', )
    raw_id_fields = ('credential', )

    class Meta:
        model = CurrentBalance

admin.site.register(CurrentBalance, CurrentBalanceAdmin)


class SellBTCOrderAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential',
            'custom_code',
            'satoshis',
            'currency_code',
            'fees_in_fiat',
            'to_receive_in_fiat',
            )
    raw_id_fields = ('credential', )

    class Meta:
        model = SellBTCOrder

admin.site.register(SellBTCOrder, SellBTCOrderAdmin)


class SentBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential',
            'txn_hash',
            'satoshis',
            'destination_btc_address',
            'destination_email',
            'unique_id',
            'notes',
            'status',
            'status_last_checked_at',
            )
    raw_id_fields = ('credential', )

    class Meta:
        model = SentBTC

admin.site.register(SentBTC, SentBTCAdmin)
