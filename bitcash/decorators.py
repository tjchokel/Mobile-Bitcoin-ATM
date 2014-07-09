from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.core.urlresolvers import reverse


class is_merchant_admin_page(object):

    def __init__(self, func):
        self.func = func

    def __call__(self, request, *args, **kwargs):
        last_password_validation = request.session.get('last_password_validation')
        if not last_password_validation:
            return HttpResponseRedirect(reverse('password_prompt'))
        return self.func(request, *args, **kwargs)


class reset_admin_password_validation(object):

    def __init__(self, func):
        self.func = func

    def __call__(self, request, *args, **kwargs):
        request.session['last_password_validation'] = None
        return self.func(request, *args, **kwargs)