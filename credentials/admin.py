from django.contrib import admin
from credentials.models import (BaseCredential, BaseSellBTC, BaseBalance,
        BaseAddressFromCredential, BaseSentBTC)

from utils import format_satoshis_with_units


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

    def satoshis_formatted(self, instance):
        return format_satoshis_with_units(instance.satoshis)
    satoshis_formatted.allow_tags = True

    list_display = ('id', 'created_at', 'credential', 'satoshis_formatted', )
    raw_id_fields = ('credential', )

    class Meta:
        model = BaseBalance

admin.site.register(BaseBalance, BaseBalanceAdmin)


class BaseAddressFromCredentialAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'created_at',
            'credential',
            'b58_address',
            'retired_at',
            )
    raw_id_fields = ('credential', )

    class Meta:
        model = BaseAddressFromCredential

admin.site.register(BaseAddressFromCredential, BaseAddressFromCredentialAdmin)


class BaseSellBTCAdmin(admin.ModelAdmin):

    def satoshis_formatted(self, instance):
        return format_satoshis_with_units(instance.satoshis)
    satoshis_formatted.allow_tags = True

    list_display = (
            'id',
            'created_at',
            'credential',
            'satoshis_formatted',
            'currency_code',
            'fees_in_fiat',
            'to_receive_in_fiat',
            )
    raw_id_fields = ('credential', )

    class Meta:
        model = BaseSellBTC

admin.site.register(BaseSellBTC, BaseSellBTCAdmin)


class BaseSentBTCAdmin(admin.ModelAdmin):

    def satoshis_formatted(self, instance):
        return format_satoshis_with_units(instance.satoshis)
    satoshis_formatted.allow_tags = True

    list_display = (
            'id',
            'created_at',
            'credential',
            'txn_hash',
            'satoshis_formatted',
            'destination_btc_address',
            'destination_email',
            )
    raw_id_fields = ('credential', )

    class Meta:
        model = BaseSentBTC

admin.site.register(BaseSentBTC, BaseSentBTCAdmin)
