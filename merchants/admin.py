from django.contrib import admin
from merchants.models import Merchant, AppUser


class AppUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email',
        'phone_num', 'username'
    )

    class Meta:
        model = AppUser

admin.site.register(AppUser, AppUserAdmin)


class MerchantAdmin(admin.ModelAdmin):

    def btc_address(self, instance):
        return instance.get_destination_address()
    btc_address.allow_tags = True

    list_display = (
        'id',
        'business_name',
        'currency_code',
        'btc_address',
        'address_1',
        'address_2',
        'city',
        'country',
        'zip_code',
        'phone_num',
        'basis_points_markup',
        'hours',
    )
    raw_id_fields = ('app_user', )

    class Meta:
        model = Merchant

admin.site.register(Merchant, MerchantAdmin)
