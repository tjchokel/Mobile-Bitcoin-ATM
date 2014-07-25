from django.http import HttpResponseRedirect
from django.contrib import messages
import json

from bitcash.settings import MERCHANT_LOGIN_REQUIRED_PATHS, MERCHANT_LOGIN_PW_URL


class MerchantAdminSectionMiddleware(object):
    def process_request(self, request):
        if request.path in MERCHANT_LOGIN_REQUIRED_PATHS:
            if request.session.get('last_password_validation'):
                # TODO: maybe make it so that it has to be recent?
                return None
            else:
                redirect_url = '%s?next=%s' % (MERCHANT_LOGIN_PW_URL, request.path.strip('/'))
                return HttpResponseRedirect(redirect_url)
        elif request.is_ajax():
            return None
        else:
            request.session['last_password_validation'] = None
            return None


class SSLMiddleware(object):
    # http://stackoverflow.com/a/9207726/1754586

    def process_request(self, request):
        if not any([request.is_secure(), request.META.get("HTTP_X_FORWARDED_PROTO", "") == 'https']):
            url = request.build_absolute_uri(request.get_full_path())
            secure_url = url.replace("http://", "https://")
            return HttpResponseRedirect(secure_url)


# http://hunterford.me/django-messaging-for-ajax-calls-using-jquery/
class AjaxMessaging(object):
    def process_response(self, request, response):
        if request.is_ajax():
            if response['Content-Type'] in ["application/javascript", "application/json"]:
                try:
                    content = json.loads(response.content)
                except ValueError:
                    return response

                django_messages = []

                for message in messages.get_messages(request):
                    django_messages.append({
                        "level": message.level,
                        "message": message.message,
                        "extra_tags": message.tags,
                    })

                content['django_messages'] = django_messages
                response.content = json.dumps(content)

        return response
