from django.contrib import admin

from shoppers.models import Shopper


class ShopperAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'email',
        'phone_num',
    )

    class Meta:
        model = Shopper

admin.site.register(Shopper, ShopperAdmin)
