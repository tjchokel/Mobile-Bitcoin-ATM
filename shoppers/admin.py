from django.contrib import admin

from shoppers.models import Shopper

from bitcash.custom import ReadOnlyModelAdmin


class ShopperAdmin(ReadOnlyModelAdmin):

    list_display = (
        'id',
        'name',
        'email',
        'phone_num',
    )

    class Meta:
        model = Shopper

admin.site.register(Shopper, ShopperAdmin)
