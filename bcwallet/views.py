from django.http import HttpResponse
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.contrib import messages
from annoying.decorators import render_to
from django.utils.timezone import now

from bcwallet.forms import BlockchainAPIForm
from bcwallet.models import BCICredential


@login_required
@render_to('merchants/blockchain.html')
def blockchain(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_blockchain_credentials()

    form = BlockchainAPIForm()
    if request.method == 'POST' and merchant:
        form = BlockchainAPIForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            main_password = form.cleaned_data['main_password']
            second_password = form.cleaned_data['second_password']
            credential, created = BCICredential.objects.get_or_create(
                    merchant=merchant,
                    username=username,
                    main_password=main_password,
                    second_password=second_password,
            )
            try:
                balance = credential.get_balance()
                messages.success(request, _('Your Blockchain API info has been updated'))
            except:
                credential.disabled_at = now()
                credential.save()
                messages.warning(request, _('Your Blockchain API credentials are not valid'))

            return HttpResponseRedirect(reverse_lazy('blockchain'))

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
    credential = merchant.get_blockchain_credentials()
    try:
        balance = credential.get_balance()
        messages.success(request, _('Your Blockchain API info has been refreshed'))
    except:
        messages.warning(request, _('Your Blockchain API info could not be validated'))
    return HttpResponse("*ok*")


@login_required
def disable_credentials(request):
    user = request.user
    merchant = user.get_merchant()
    credential = merchant.get_blockchain_credentials()
    credential.disabled_at = now()
    credential.save()
    return HttpResponse("*ok*")