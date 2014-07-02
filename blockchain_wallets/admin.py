from django.contrib import admin

from blockchain_wallets.models import BCICredential


class BCICredentialAdmin(admin.ModelAdmin):

    list_display = ('id', 'username', 'main_password', 'second_password', )

    class Meta:
        model = BCICredential

admin.site.register(BCICredential, BCICredentialAdmin)
