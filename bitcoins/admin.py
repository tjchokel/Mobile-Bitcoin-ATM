from django.contrib import admin
from bitcoins.models import BTCTransaction, BTCAddress


class BTCAddressAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'b58_address', 'revealed_to_user_at'
    )

    class Meta:
        model = BTCAddress

admin.site.register(BTCAddress, BTCAddressAdmin)


class BTCTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'satoshis'
    )

    class Meta:
        model = BTCTransaction

admin.site.register(BTCTransaction, BTCTransactionAdmin)

