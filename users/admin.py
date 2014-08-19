from django.contrib import admin

from users.models import AuthUser, FutureShopper, EmailAuthToken


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


class EmailAuthTokenAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'auth_user',
        'ip_address',
        'verif_key',
        'key_used_at',
        'key_expires_at',
    )
    raw_id_fields = ('auth_user', )

    class Meta:
        model = EmailAuthToken

admin.site.register(EmailAuthToken, EmailAuthTokenAdmin)
