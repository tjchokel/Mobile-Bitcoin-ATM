from django.contrib import admin
from bitcoins.models import DestinationAddress, ForwardingAddress, BTCTransaction, ShopperBTCPurchase

from bitcash.custom import ReadOnlyModelAdmin

from utils import format_satoshis_with_units


class DestinationAddressAdmin(ReadOnlyModelAdmin):
    list_display = (
            'id',
            'uploaded_at',
            'b58_address',
            'retired_at',
            'merchant',
            'credential',
            )
    raw_id_fields = ('merchant', 'credential', )

    class Meta:
        model = DestinationAddress

admin.site.register(DestinationAddress, DestinationAddressAdmin)


class ForwardingAddressAdmin(ReadOnlyModelAdmin):
    list_display = (
            'id',
            'generated_at',
            'customer_confirmed_deposit_at',
            'b58_address',
            'paid_out_at',
            'destination_address',
            'cancelled_at',
            'merchant',
            'shopper',
            'last_activity_check_at',
            )
    raw_id_fields = ('merchant', 'shopper', 'destination_address', )

    class Meta:
        model = ForwardingAddress

admin.site.register(ForwardingAddress, ForwardingAddressAdmin)


class BTCTransactionAdmin(ReadOnlyModelAdmin):

    def satoshis_formatted(self, instance):
        return format_satoshis_with_units(instance.satoshis)
    satoshis_formatted.allow_tags = True

    list_display = (
        'id',
        'txn_hash',
        'satoshis_formatted',
        'conf_num',
        'irreversible_by',
        'suspected_double_spend_at',
        'forwarding_address',
        'destination_address',
        'fiat_amount',
        'currency_code_when_created',
        'met_minimum_confirmation_at',
        'min_confirmations_overrode_at',
        'met_confidence_threshold_at',
    )
    raw_id_fields = ('forwarding_address', 'destination_address', )

    class Meta:
        model = BTCTransaction

admin.site.register(BTCTransaction, BTCTransactionAdmin)


class ShopperBTCPurchaseAdmin(ReadOnlyModelAdmin):

    def satoshis_formatted(self, instance):
        return format_satoshis_with_units(instance.satoshis)
    satoshis_formatted.allow_tags = True

    list_display = (
        'id',
        'added_at',
        'merchant',
        'shopper',
        'b58_address',
        'fiat_amount',
        'satoshis_formatted',
        'currency_code_when_created',
        'confirmed_by_merchant_at',
        'cancelled_at',
        'funds_sent_at',
        'expires_at',
        'credential',
        'btc_transaction',
        'merchant_email_sent_at',
        'shopper_email_sent_at',
    )
    raw_id_fields = ('merchant', 'shopper', 'credential', 'btc_transaction', 'base_sent_btc', )

    class Meta:
        model = ShopperBTCPurchase

admin.site.register(ShopperBTCPurchase, ShopperBTCPurchaseAdmin)
