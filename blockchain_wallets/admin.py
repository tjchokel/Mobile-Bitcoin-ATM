from django.contrib import admin

from blockchain_wallets.models import BCICredential, BCISentBTC

from bitcash.custom import ReadOnlyModelAdmin


class BCICredentialAdmin(ReadOnlyModelAdmin):

    list_display = (
            'id',
            'merchant',
            'disabled_at',
            'last_succeded_at',
            'last_failed_at',
            'username',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = BCICredential

admin.site.register(BCICredential, BCICredentialAdmin)


class BCISentBTCAdmin(ReadOnlyModelAdmin):

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
