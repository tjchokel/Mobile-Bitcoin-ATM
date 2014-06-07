from django.contrib import admin
from bitcoins.models import DestinationAddress, ForwardingAddress, BTCTransaction


class DestinationAddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'uploaded_at', 'b58_address', 'retired_at', 'merchant')

    class Meta:
        model = DestinationAddress

admin.site.register(DestinationAddress, DestinationAddressAdmin)


class ForwardingAddressAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'generated_at',
            'b58_address',
            'retired_at',
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
    )

    class Meta:
        model = BTCTransaction

admin.site.register(BTCTransaction, BTCTransactionAdmin)
