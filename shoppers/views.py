from django.http import HttpResponseRedirect
from django.views.decorators.debug import sensitive_variables, sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages

from annoying.decorators import render_to

from bitcoins.models import ShopperBTCPurchase
from shoppers.models import Shopper

from shoppers.forms import ShopperInformationForm, BuyBitcoinForm, NoEmailBuyBitcoinForm, ConfirmPasswordForm

from emails.trigger import send_admin_email


@sensitive_variables('password', 'password_form')
@sensitive_post_parameters('password', )
@login_required
@render_to('customer_dash/main.html')
def customer_dashboard(request):
    user = request.user
    if user.is_superuser:
        return HttpResponseRedirect(reverse_lazy('admin:index'))

    merchant = user.get_merchant()
    if not merchant or not merchant.has_destination_address():
        return HttpResponseRedirect(reverse_lazy('register_router'))
    transactions, shopper = None, None
    forwarding_address_obj = merchant.get_latest_forwarding_obj()
    btc_purchase_request = merchant.get_bitcoin_purchase_request()

    if btc_purchase_request and btc_purchase_request.is_cancelled():
        # Defensive check on cash-in, can't think of when this *should* happen
        msg = _('Sorry, that request was cancelled. Please contact us if that was not intentional.')
        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))

    credential = merchant.get_valid_api_credential()

    if credential and credential.is_coinbase_credential():
        buy_form = BuyBitcoinForm(initial={'email_or_btc_address': '1'}, merchant=merchant)
    else:
        buy_form = NoEmailBuyBitcoinForm(merchant=merchant)
    password_form = ConfirmPasswordForm(user=user)
    shopper_form = ShopperInformationForm()
    override_confirmation_form = ConfirmPasswordForm(user=user)
    show_buy_modal, show_confirm_purchase_modal, show_override_confirmations_modal = 'false', 'false', 'false'
    if forwarding_address_obj:
        # In case of refreshing the page later
        # Will be None on first use and be overwritten below
        shopper = forwarding_address_obj.shopper
        transactions = forwarding_address_obj.get_all_forwarding_transactions()
    if request.method == 'POST':
        # if submitting a buy bitcoin form
        if 'amount' in request.POST:
            if credential and credential.is_coinbase_credential():
                buy_form = BuyBitcoinForm(data=request.POST, merchant=merchant)
            else:
                buy_form = NoEmailBuyBitcoinForm(data=request.POST, merchant=merchant)
            if buy_form.is_valid():
                if credential.is_coinbase_credential():
                    email_or_btc_address = buy_form.cleaned_data['email_or_btc_address']
                else:
                    email_or_btc_address = None
                amount = buy_form.cleaned_data['amount']
                email = buy_form.cleaned_data['email']
                btc_address = buy_form.cleaned_data['btc_address']
                # Create shopper object
                shopper = Shopper.objects.create(
                    email=email,
                )

                # if sending to email
                if email_or_btc_address and email_or_btc_address == '1':
                    ShopperBTCPurchase.objects.create(
                        merchant=merchant,
                        shopper=shopper,
                        fiat_amount=amount,
                        credential=credential,
                    )
                else:
                    ShopperBTCPurchase.objects.create(
                        merchant=merchant,
                        shopper=shopper,
                        fiat_amount=amount,
                        b58_address=btc_address,
                        credential=credential,
                    )

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
            else:
                show_buy_modal = 'true'
        # if submitting shopper form
        elif 'name' in request.POST:
            shopper_form = ShopperInformationForm(data=request.POST)
            if shopper_form.is_valid():

                name = shopper_form.cleaned_data['name']
                email = shopper_form.cleaned_data['email']

                # Create shopper object
                shopper = Shopper.objects.create(
                    name=name,
                    email=email,
                )

                forwarding_address_obj.shopper = shopper
                forwarding_address_obj.save()

                # Fetch existing TXs if they exist
                existing_txns = forwarding_address_obj.get_all_forwarding_transactions()

                # If we have a confirmed TX then send a notification to the shopper
                # (they were unable to receive a notification at confirmation time because we didn't yet have their info)
                for existing_txn in existing_txns:
                    if existing_txn.is_confirmed():
                        existing_txn.send_shopper_txconfirmed_email()

                return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
        # if submitting password confirmation form
        elif 'password' in request.POST:
            if btc_purchase_request:
                # cash in scenario, sending bitcoin to shopper
                password_form = ConfirmPasswordForm(user=user, data=request.POST)
                if password_form.is_valid():
                    btc_purchase_request_updated, api_call, err_str = btc_purchase_request.pay_out_bitcoin(send_receipt=True)
                    if err_str:
                        if api_call:
                            api_call.send_admin_btcpurchase_error_email(btc_purchase_request_updated)
                        else:
                            # These errors are OK to include in plaintext emails, they messages are written by us
                            body_context = {
                                    'coinsafe_err_str': err_str,
                                    'shopper_request_url': reverse_lazy(
                                        'admin:bitcoins_shopperbtcpurchase_change',
                                        args=(btc_purchase_request.id, )
                                        )
                                    }
                            send_admin_email(
                                    body_template='btc_purchase_not_attempted_notification.html',
                                    subject='Non API Error for Shopper BTC Purchase Request %s' % btc_purchase_request.id,
                                    body_context=body_context,
                                    )
                        show_confirm_purchase_modal = 'false'
                        msg = _('Bitcoin sending failed. The API returned the following error: %s' % err_str)
                        messages.warning(request, msg)
                        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                    else:
                        msg = _('Success! Your bitcoin is being sent. A receipt will be emailed to %s' % btc_purchase_request.shopper.email)
                        messages.success(request, msg)
                        return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    show_confirm_purchase_modal = 'true'
            else:
                # cash out scenario, overriding required confirmations
                override_confirmation_form = ConfirmPasswordForm(user=user, data=request.POST)
                if override_confirmation_form.is_valid():
                    if transactions:
                        # Possible corner case where a person could have two
                        # tabs open and override the transaction in the other tab.
                        # Then they wouldn't have any transactions in this tab
                        for transaction in transactions:
                            # Having a transactions array is confusing, but it's
                            # possible a person would send BTC in multiple transactions
                            transaction.set_merchant_confirmation_override()
                    return HttpResponseRedirect(reverse_lazy('customer_dashboard'))
                else:
                    show_override_confirmations_modal = 'true'

    if forwarding_address_obj:
        txn_group_payload = forwarding_address_obj.get_txn_group_payload()
    else:
        txn_group_payload = None

    return {
        'user': user,
        'merchant': merchant,
        'current_address': forwarding_address_obj,
        'transactions': transactions,
        'txn_group_payload': txn_group_payload,
        'shopper': shopper,
        'buy_request': btc_purchase_request,
        'password_form': password_form,
        'shopper_form': shopper_form,
        'buy_form': buy_form,
        'override_confirmation_form': override_confirmation_form,
        'show_buy_modal': show_buy_modal,
        'show_confirm_purchase_modal': show_confirm_purchase_modal,
        'show_override_confirmations_modal': show_override_confirmations_modal,
    }
