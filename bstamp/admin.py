from django.contrib import admin
from bstamp.models import BSCredential, BSBalance, BSSendBTC


class BSCredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'merchant',
            'username',
            'api_key',
            'disabled_at',
            'last_succeded_at',
            'last_failed_at',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = BSCredential

admin.site.register(BSCredential, BSCredentialAdmin)


class BSBalanceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'bs_credential', 'satoshis', )
    raw_id_fields = ('bs_credential', )

    class Meta:
        model = BSBalance

admin.site.register(BSBalance, BSBalanceAdmin)


class BSSendBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'bs_credential',
            'bs_withdrawal_id',
            'satoshis',
            'destination_address',
            'status',
            'status_last_checked_at',
            )
    raw_id_fields = ('bs_credential', )

    class Meta:
        model = BSSendBTC

admin.site.register(BSSendBTC, BSSendBTCAdmin)
