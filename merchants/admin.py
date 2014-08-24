from django.contrib import admin
from merchants.models import Merchant, OpenTime, MerchantWebsite


def set_latitude_longitude(modeladmin, request, queryset):
    for obj in queryset:
        obj.set_latitude_longitude()
set_latitude_longitude.short_description = "Set Latitiude and Longitude"


class MerchantAdmin(admin.ModelAdmin):

    def btc_address(self, instance):
        return instance.get_destination_address()
    btc_address.allow_tags = True

    def website(self, instance):
        return instance.get_website_obj()
    website.allow_tags = True

    def short_url(self, instance):
        short_url_obj = instance.get_short_url_obj()
        if short_url_obj:
            profile_uri = short_url_obj.get_profile_uri()
            if profile_uri:
                return '<a href="%s">%s</a> (<a href="%s">edit</a> or <a href="%s">add</a>)' % (
                        profile_uri, profile_uri,
                        short_url_obj.get_admin_uri(),
                        short_url_obj.get_new_admin_uri()
                        )
        return ''
    short_url.allow_tags = True

    list_display = (
        'id',
        'created_at',
        'business_name',
        'short_url',
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
        'latitude_position',
        'longitude_position',
        'ignored_at',
    )
    raw_id_fields = ('user', )

    class Meta:
        model = Merchant
    actions = [set_latitude_longitude]
admin.site.register(Merchant, MerchantAdmin)


class OpenTimeAdmin(admin.ModelAdmin):

    list_display = ('id', 'merchant', 'weekday', 'from_time', 'to_time', 'is_closed_this_day')
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
