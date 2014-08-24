from django.contrib import admin

from services.models import APICall, WebHook


class APICallAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'created_at',
            'api_name',
            'url_hit',
            'response_code',
            'post_params',
            'headers',
            'api_results',
            'merchant',
            'credential',
            )
    # https://coderwall.com/p/ppqusg
    raw_id_fields = ('merchant', 'credential', )

    class Meta:
        model = APICall
admin.site.register(APICall, APICallAdmin)


class WebHookAdmin(admin.ModelAdmin):
    list_display = (
            'id',
            'created_at',
            'ip_address',
            'user_agent',
            'api_name',
            'hostname',
            'request_path',
            'merchant',
            'uses_https',
            'data_from_get',
            'data_from_post',
            )

    class Meta:
        model = WebHook
admin.site.register(WebHook, WebHookAdmin)
