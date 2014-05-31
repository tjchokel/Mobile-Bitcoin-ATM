from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


class confirm_registration_eligible(object):

    def __init__(self, func):
        self.func = func

    def __call__(self, request, *args, **kwargs):

        user = request.user

        if user.get_registration_step() > 2:
            return HttpResponseRedirect(reverse('customer_dashboard'))

        return self.func(request, *args, **kwargs)