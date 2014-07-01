from django.contrib import admin
from credentials.models import BaseCredential, BaseSellBTC, BaseBalance, BaseSentBTC


class BaseCredentialAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'merchant',
            'last_succeded_at',
            'last_failed_at',
            'disabled_at',
            )
    raw_id_fields = ('merchant', )

    class Meta:
        model = BaseCredential

admin.site.register(BaseCredential, BaseCredentialAdmin)


class BaseBalanceAdmin(admin.ModelAdmin):

    list_display = ('id', 'created_at', 'credential_link', 'satoshis', )
    raw_id_fields = ('credential_link', )

    class Meta:
        model = BaseBalance

admin.site.register(BaseBalance, BaseBalanceAdmin)


class BaseSellBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential_link',
            'satoshis',
            'currency_code',
            'fees_in_fiat',
            'to_receive_in_fiat',
            )
    raw_id_fields = ('credential_link', )

    class Meta:
        model = BaseSellBTC

admin.site.register(BaseSellBTC, BaseSellBTCAdmin)


class BaseSentBTCAdmin(admin.ModelAdmin):

    list_display = (
            'id',
            'created_at',
            'credential_link',
            'txn_hash',
            'satoshis',
            'destination_btc_address',
            'destination_email',
            )
    raw_id_fields = ('credential_link', )

    class Meta:
        model = BaseSentBTC

admin.site.register(BaseSentBTC, BaseSentBTCAdmin)
