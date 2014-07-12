from django.contrib import admin
from bitcoins.models import DestinationAddress, ForwardingAddress, BTCTransaction, ShopperBTCPurchase


class DestinationAddressAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'uploaded_at',
            'b58_address',
            'retired_at',
            'merchant',
            'credential',
            )

    class Meta:
        model = DestinationAddress

admin.site.register(DestinationAddress, DestinationAddressAdmin)


class ForwardingAddressAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'generated_at',
            'b58_address',
            'paid_out_at',
            'destination_address',
            'merchant',
            )

    class Meta:
        model = ForwardingAddress

admin.site.register(ForwardingAddress, ForwardingAddressAdmin)


class BTCTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'txn_hash',
        'satoshis',
        'conf_num',
        'irreversible_by',
        'suspected_double_spend_at',
        'forwarding_address',
        'destination_address',
        'fiat_amount',
        'currency_code_when_created',
        'met_minimum_confirmation_at',
        'min_confirmations_overrode_at'
    )

    class Meta:
        model = BTCTransaction

admin.site.register(BTCTransaction, BTCTransactionAdmin)


class ShopperBTCPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'merchant',
        'b58_address',
        'fiat_amount',
        'satoshis',
        'currency_code_when_created',
        'confirmed_by_merchant_at',
        'expires_at',
        'cancelled_at',
    )

    class Meta:
        model = ShopperBTCPurchase

admin.site.register(ShopperBTCPurchase, ShopperBTCPurchaseAdmin)
