from django.contrib import admin

from users.models import AuthUser, FutureShopper, EmailAuthToken, LoggedLogin

from bitcash.custom import ReadOnlyModelAdmin


class AuthUserAdmin(ReadOnlyModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email', 'phone_num', 'username'
    )

    class Meta:
        model = AuthUser

admin.site.register(AuthUser, AuthUserAdmin)


class LoggedLoginAdmin(ReadOnlyModelAdmin):
    list_display = (
        'id', 'login_at', 'auth_user', 'ip_address', 'user_agent',
    )
    raw_id_fields = ('auth_user', )

    class Meta:
        model = LoggedLogin

admin.site.register(LoggedLogin, LoggedLoginAdmin)


class FutureShopperAdmin(ReadOnlyModelAdmin):
    list_display = (
        'id', 'email', 'city', 'country', 'intention', 'subscribed_at',
    )
    list_filter = ('intention', 'country', )

    class Meta:
        model = FutureShopper

admin.site.register(FutureShopper, FutureShopperAdmin)


class EmailAuthTokenAdmin(ReadOnlyModelAdmin):
    list_display = (
        'id',
        'created_at',
        'auth_user',
        'ip_address',
        'verif_key',
        'key_used_at',
        'key_expires_at',
        'key_deleted_at',
    )
    raw_id_fields = ('auth_user', )

    class Meta:
        model = EmailAuthToken

admin.site.register(EmailAuthToken, EmailAuthTokenAdmin)
