from django.contrib import admin

from users.models import AuthUser, FutureShopper


class AuthUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email', 'phone_num', 'username'
    )

    class Meta:
        model = AuthUser

admin.site.register(AuthUser, AuthUserAdmin)


class FutureShopperAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'email', 'city', 'country', 'intention'
    )

    class Meta:
        model = FutureShopper

admin.site.register(FutureShopper, FutureShopperAdmin)
