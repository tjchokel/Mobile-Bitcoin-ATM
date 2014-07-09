from django.contrib import admin

from users.models import AuthUser, CustomerToBeNotified


class AuthUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email',
        'phone_num', 'username'
    )

    class Meta:
        model = AuthUser

admin.site.register(AuthUser, AuthUserAdmin)


class CustomerToBeNotifiedAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'email', 'city', 'country',
        'intention'
    )

    class Meta:
        model = CustomerToBeNotified

admin.site.register(CustomerToBeNotified, CustomerToBeNotifiedAdmin)
