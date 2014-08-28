from django.http import HttpResponseRedirect
from django.contrib import messages
import json

from bitcash.settings import MERCHANT_LOGIN_REQUIRED_PATHS, MERCHANT_LOGIN_PW_URL, LOGIN_URL
from users.models import AuthUser
from emails.trigger import add_qs


class MerchantAdminSectionMiddleware(object):
    def process_request(self, request):
        if request.path in MERCHANT_LOGIN_REQUIRED_PATHS:
            # Pass redirection querystring to login page when about to login:
            if not request.user.is_authenticated():
                # Build next url and email querystring
                qs_dict = {'next': request.path.strip('/')}
                if request.GET.get('e'):
                    qs_dict['e'] = request.GET.get('e')
                redirect_url = add_qs(LOGIN_URL, qs_dict)
                return HttpResponseRedirect(redirect_url)

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


# http://stackoverflow.com/questions/2242909/django-user-impersonation-by-admin
class ImpersonateMiddleware(object):
    def process_request(self, request):
        if request.user.is_superuser and "__impersonate" in request.GET:
            request.session['impersonate_username'] = request.GET["__impersonate"]
        elif "__unimpersonate" in request.GET:
            if 'impersonate_username' in request.session:
                del request.session['impersonate_username']
        if request.user.is_superuser and 'impersonate_username' in request.session:
            request.user = AuthUser.objects.get(username=request.session['impersonate_username'])
