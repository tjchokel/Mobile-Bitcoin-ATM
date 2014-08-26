from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.core.urlresolvers import reverse

from annoying.functions import get_object_or_None

from merchants.models import Merchant
from emails.models import SentEmail
from emails.trigger import send_and_log, test_mail_merge

from optparse import make_option
from datetime import timedelta

from utils import dp


def custom_confirm(body_template, incomplete_merchant):
    '''
    Helper function to confirm an action. Defaults to Yes.

    Return True if response is affirmative, False if response is negative.
    '''
    confirm = raw_input('Send %s to %s (%s)? [Y/n]: ' % (body_template,
        incomplete_merchant, incomplete_merchant.user.email))

    if confirm.lower().startswith('n'):
        # N/n/No/no/etc
        return False
    return True


def send_nag_email(body_template, incomplete_merchant, subject, context_dict={}):
    ''' Returns true if we should send and false otherwise '''

    # TODO: abstract this
    from_name = 'Michael Flaxman'
    from_email = 'michael@coinsafe.com'

    test_mail_merge(body_template=body_template, context_dict=context_dict)

    bt_clean = body_template.split('/')[-1]

    sent_email = get_object_or_None(SentEmail, body_template=body_template,
            to_merchant=incomplete_merchant)

    if sent_email:
        dp("Did NOT send %s to %s (already sent on %s)" % (
            bt_clean, incomplete_merchant, sent_email.sent_at))
        return

    recent_time = now() - timedelta(hours=48)
    num_recent_emails = SentEmail.objects.filter(sent_at__gt=recent_time,
            to_merchant=incomplete_merchant).count()
    if num_recent_emails > 0:
        dp("Did NOT send %s to %s (recently contacted about something else)" % (
            bt_clean, incomplete_merchant))
        return

    if not custom_confirm(bt_clean, incomplete_merchant):
        dp("Did NOT send %s to %s" % (bt_clean, incomplete_merchant))
        return

    dp('Sending %s to %s...' % (bt_clean, incomplete_merchant))
    return send_and_log(
            subject=subject,
            to_merchant=incomplete_merchant,
            body_template=body_template,
            body_context=context_dict,
            from_name=from_name,
            from_email=from_email,
            #cc_name='CoinSafe Support',
            #cc_email='support@coinsafe.com',
            is_transactional=False,
            )


class Command(BaseCommand):
    help = " Sends nag emails based on where users are in the onboarding "
    option_list = BaseCommand.option_list + (
        make_option('--verbose',
            dest='verbose',
            default=True,
            help='Print stats as script runs'),
    )

    def handle(self, verbose, *args, **kwargs):
        dp("Starting command...")

        min_signup_time = now() - timedelta(days=30)
        max_signup_time = now() - timedelta(hours=3)

        recent_merchants = Merchant.objects.filter(
                ignored_at=None,
                created_at__gt=min_signup_time,
                created_at__lt=max_signup_time,
                ).order_by('created_at')

        dp('%s merchant signups to try...' % recent_merchants.count())
        for recent_merchant in recent_merchants:

            api_cred = recent_merchant.get_valid_api_credential()
            if not api_cred:
                context_dict = {
                        'store_name': recent_merchant.business_name,
                        'finish_register_uri': reverse('register_bitcoin'),
                        }
                body_template = 'drip/no_credentials.html'
                subject = 'Your Bitcoin ATM is Almost Ready'
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            if not recent_merchant.address_1:
                context_dict = {
                        'store_name': recent_merchant.business_name,
                        'profile_edit_uri': reverse('merchant_profile'),
                        }
                body_template = 'drip/no_address.html'
                subject = "Where is %s?" % (recent_merchant.business_name)
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            context_dict['promotional_material_uri'] = reverse('promotional_material')
            context_dict['store_name'] = recent_merchant.business_name
            context_dict['api_name'] = api_cred.get_credential_to_display()

            balance = api_cred.get_balance()
            if balance is False:
                # TODO: move this to a better URL when we have one
                context_dict['api_cred_uri'] = reverse('merchant_profile')
                body_template = 'drip/bad_api_credential.html'
                subject = 'Your %s API Credentials Are No Longer Valid' % context_dict['api_name']
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            if balance == 0:
                # TODO: move this to a better URL when we have one
                context_dict['fund_wallet_uri'] = reverse('merchant_profile')
                body_template = 'drip/no_balance.html'
                subject = 'Fund Your Bitcoin ATM So You Can Sell Bitcoin to Customers'
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            has_phone = bool(recent_merchant.phone_num)
            has_logo = recent_merchant.has_doc_obj()
            has_website = recent_merchant.has_website()

            context_dict['profile_uri'] = recent_merchant.get_profile_uri()

            if not has_phone:
                # TODO: move this to a better URL when we have one
                context_dict['add_phone_uri'] = reverse('merchant_profile')

                body_template = 'drip/no_phone.html'
                subject = "What Is the Phone Number at %s?" % recent_merchant.business_name
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            if not has_logo:
                # TODO: move this to a better URL when we have one
                context_dict['add_logo_uri'] = reverse('merchant_profile')

                body_template = 'drip/no_logo.html'
                subject = "Does %s Have a Logo?" % recent_merchant.business_name
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            if not has_website:
                body_template = 'drip/no_website.html'
                subject = "Does %s Have a Website?" % recent_merchant.business_name
                send_nag_email(
                        subject=subject,
                        body_template=body_template,
                        incomplete_merchant=recent_merchant,
                        context_dict=context_dict,
                        )
                continue

            # TODO: add link to us request (for those with websites)

            # None applicable
            msg = "Not contacting %s because they're all good!" % recent_merchant
            dp(msg)

        dp('All done!')
