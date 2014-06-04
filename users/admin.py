from django.contrib import admin

from users.models import AuthUser


class AuthUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email',
        'phone_num', 'username'
    )

    class Meta:
        model = AuthUser

admin.site.register(AuthUser, AuthUserAdmin)
