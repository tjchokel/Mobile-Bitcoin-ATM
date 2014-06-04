from django.contrib import admin

from users.models import CashUser


class CashUserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'email',
        'phone_num', 'username'
    )

    class Meta:
        model = CashUser

admin.site.register(CashUser, CashUserAdmin)
