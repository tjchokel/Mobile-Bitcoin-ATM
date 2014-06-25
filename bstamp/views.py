from django.http import HttpResponse
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from annoying.decorators import render_to
from django.utils.timezone import now

from bstamp.forms import BitstampAPIForm
from bstamp.models import BSCredential


@login_required
@render_to('merchants/bitstamp.html')
def bitstamp(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credentials()

    form = BitstampAPIForm()
    if request.method == 'POST' and merchant:
        form = BitstampAPIForm(data=request.POST)
        if form.is_valid():
            api_key = form.cleaned_data['api_key']
            secret_key = form.cleaned_data['secret_key']
            username = form.cleaned_data['username']
            credential, created = BSCredential.objects.get_or_create(
                    merchant=merchant,
                    username=username,
                    api_key=api_key,
                    api_secret=secret_key
            )
            try:
                balance = credential.get_balance()
                messages.success(request, _('Your Bitstamp API info has been updated'))
            except:
                credential.disabled_at = now()
                credential.save()
                messages.warning(request, _('Your Bitstamp API credentials are not valid'))

            return HttpResponseRedirect(reverse_lazy('bitstamp'))

    return {
        'user': user,
        'merchant': merchant,
        'form': form,
        'on_admin_page': True,
        'credential': credential,
    }


@login_required
def refresh_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credentials()
    try:
        balance = credential.get_balance()
        messages.success(request, _('Your Bistamp API info has been refreshed'))
    except:
        messages.warning(request, _('Your Bistamp API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def disable_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_bitstamp_credentials()
    credential.disabled_at = now()
    credential.save()
    return HttpResponse("*ok*")