from django.contrib import admin
from business.models import Business, AppUser


class AppUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email',
        'phone_num', 'username'
    )

    class Meta:
        model = AppUser

admin.site.register(AppUser, AppUserAdmin)


class BusinessAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'business_name', 'currency_code', 'address_1', 'address_2',
        'city', 'country', 'zip_code', 'phone_num', 'hours'
    )
    raw_id_fields = ('app_user', )

    class Meta:
        model = Business

admin.site.register(Business, BusinessAdmin)
