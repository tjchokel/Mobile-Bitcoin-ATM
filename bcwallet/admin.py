from django.contrib import admin
from bcwallet.models import BCICredential, BCIBalance, BCISendBTC


class BCICredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'merchant',
            'last_succeded_at',
            'last_failed_at',
            'disabled_at',
            'username',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = BCICredential

admin.site.register(BCICredential, BCICredentialAdmin)


class BCIBalanceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'bci_credential', 'satoshis', )
    raw_id_fields = ('bci_credential', )

    class Meta:
        model = BCIBalance

admin.site.register(BCIBalance, BCIBalanceAdmin)


class BCISendBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'bci_credential',
            'satoshis',
            'destination_address',
            'tx_hash',
            )
    raw_id_fields = ('bci_credential', )

    class Meta:
        model = BCISendBTC

admin.site.register(BCISendBTC, BCISendBTCAdmin)
