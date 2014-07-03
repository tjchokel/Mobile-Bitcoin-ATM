from django.contrib import admin

from blockchain_wallets.models import BCICredential, BCISentBTC


class BCICredentialAdmin(admin.ModelAdmin):

    list_display = ('id', 'username', 'main_password', 'second_password', )

    class Meta:
        model = BCICredential

admin.site.register(BCICredential, BCICredentialAdmin)


class BCISentBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential',
            'txn_hash',
            'satoshis',
            'destination_btc_address',
            'destination_email',
            )

    class Meta:
        model = BCISentBTC

admin.site.register(BCISentBTC, BCISentBTCAdmin)
