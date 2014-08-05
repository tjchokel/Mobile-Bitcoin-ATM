from django.contrib import admin
from merchants.models import Merchant, OpenTime, MerchantWebsite


class MerchantAdmin(admin.ModelAdmin):

    def btc_address(self, instance):
        return instance.get_destination_address()
    btc_address.allow_tags = True

    def website(self, instance):
        return instance.get_website()
    website.allow_tags = True

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
        'cashin_markup_in_bps',
        'cashout_markup_in_bps',
        'website',
    )
    raw_id_fields = ('user', )

    class Meta:
        model = Merchant

admin.site.register(Merchant, MerchantAdmin)


class OpenTimeAdmin(admin.ModelAdmin):

    list_display = ('id', 'merchant', 'weekday', 'from_time', 'to_time', )
    raw_id_fields = ('merchant', )

    class Meta:
        model = OpenTime

admin.site.register(OpenTime, OpenTimeAdmin)


class MerchantWebsiteAdmin(admin.ModelAdmin):

    list_display = ('id', 'merchant', 'url', 'deleted_at', )
    raw_id_fields = ('merchant', )

    class Meta:
        model = MerchantWebsite

admin.site.register(MerchantWebsite, MerchantWebsiteAdmin)
