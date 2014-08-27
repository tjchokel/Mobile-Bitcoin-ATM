from django.template.loader import render_to_string

from bitcash.settings import (POSTMARK_SENDER, EMAIL_DEV_PREFIX, BASE_URL,
        ADMINS, MAILGUN_API_KEY, MAILGUN_DOMAIN, BCC_DEBUG_ADDRESS)

from utils import split_email_header, cat_email_header, add_qs

# Email sending libraries
from postmark import PMMail
import requests

import re


def get_links(html):
    """
    Get all the links in some HTML.
    """
    return re.findall(r'<a href="(.*?)"', html)


def append_qs(html, qs_dict, link_text):
    """
    Take some html, find all the links and add the qs_dict to it

    To not change the html just use something that's not in this format:
      <a href="/">text</a>

    For example, this will NOT be affected (see the regex in the code):
      <a class="something" href="/">text</a>
    """
    if qs_dict:
        for old_link in get_links(html):
            if link_text in old_link:
                new_link = add_qs(old_link, qs_dict)
                new_link_fragment = '<a href="%s"' % new_link
                old_link_fragment = '<a href="%s"' % old_link
                html = html.replace(old_link_fragment, new_link_fragment)
    return html


def mailgun_send(subject, html_body, to_info, from_info, cc_info=None,
        replyto_info=None, bcc_info=None):
    data_dict = {
            "from": from_info,
            "to": to_info,
            "subject": subject,
            "html": html_body,
            }
    if cc_info:
        data_dict['cc'] = cc_info
    if bcc_info:
        data_dict['bcc'] = bcc_info
    if replyto_info:
        data_dict['h:Reply-To'] = replyto_info

    r = requests.post(
        "https://api.mailgun.net/v2/%s/messages" % MAILGUN_DOMAIN,
        auth=("api", MAILGUN_API_KEY),
        data=data_dict,
        )

    # TODO: Log these in services.models.APICall

    # Fail loudly if there is a problem
    assert str(r.status_code).startswith('2'), '%s | %s' % (r.status_code. r.content)
    return r


def postmark_send(subject, html_body, to_info, from_info, cc_info=None,
        replyto_info=None, bcc_info=None):
    " Send email via postmark "
    pm = PMMail(
            sender=from_info,
            to=to_info,
            subject=subject,
            html_body=html_body,
            cc=cc_info,
            bcc=bcc_info,
            reply_to=replyto_info,
            )
    return pm.send()


def test_mail_merge(body_template, context_dict):
    """
    Weak test to verify template fields are all in context_dict.

    Used in cases where we don't want a mail merge failing siltently.
    """
    template_content = open('templates/emails/'+body_template, 'r').read()
    variables = re.findall(r'{{(.*?)}}', template_content)
    # Trim whitespace and only take entries to the left of the first period (if applicable):
    variables = set([x.strip().split('.')[0] for x in variables])
    # Remove variable in all templates:
    variables.remove('BASE_URL')
    for variable in variables:
        if variable not in context_dict:
            raise Exception('Missing variable `%s` in `%s`' % (variable, body_template))


# TODO: create non-blocking queue system and move email sending to queue
def send_and_log(subject, body_template, to_merchant=None, to_email=None,
        to_name=None, body_context={}, from_name=None, from_email=None,
        cc_name=None, cc_email=None, replyto_name=None, replyto_email=None,
        btc_transaction=None, is_transactional=True):
    """
    Send and log an email
    """

    # TODO: find a better way to handle the circular dependency
    from emails.models import SentEmail

    if not from_email:
        from_name, from_email = split_email_header(POSTMARK_SENDER)

    body_context_modified = body_context.copy()
    body_context_modified['BASE_URL'] = BASE_URL

    if to_merchant:
        body_context_modified['salutation'] = to_merchant.user.full_name

    # Generate html body
    html_body = render_to_string('emails/'+body_template, body_context_modified)

    if to_merchant:
        # set to_name and to_email from user if neccesary
        if not to_email:
            to_email = to_merchant.user.email
        if not to_name:
            to_name = to_merchant.user.full_name

        # append ?e=email to all links in email
        html_body = append_qs(
                html=html_body,
                qs_dict={'e': to_merchant.user.email},
                link_text=BASE_URL,
                )

    send_dict = {
            'html_body': html_body,
            'from_info': cat_email_header(from_name, from_email),
            'to_info': cat_email_header(to_name, to_email),
            # These are initialized here but may be overwritten below:
            'bcc_info': BCC_DEBUG_ADDRESS,
            'subject': subject,
            }
    if cc_email:
        send_dict['cc_info'] = cat_email_header(cc_name, cc_email)
    if replyto_email:
        send_dict['replyto_info'] = cat_email_header(replyto_name, replyto_email)

    if EMAIL_DEV_PREFIX:
        send_dict['subject'] += ' [DEV]'
    else:
        if is_transactional and body_template != 'admin/contact_form.html':
            # BCC support on transactional emails (except contact us form)
            send_dict['bcc_info'] = POSTMARK_SENDER

    # Make email object
    if is_transactional:
        sent_via = SentEmail.POSTMARK
    else:
        sent_via = SentEmail.MAILGUN

    # Log everything
    se = SentEmail.objects.create(
            from_email=from_email,
            from_name=from_name,
            to_email=to_email,
            to_name=to_name,
            to_merchant=to_merchant,
            cc_name=cc_name,
            cc_email=cc_email,
            body_template=body_template,
            body_context=body_context,
            subject=subject,
            btc_transaction=btc_transaction,
            sent_via=sent_via,
            )

    if is_transactional:
        postmark_send(**send_dict)
    else:
        mailgun_send(**send_dict)

    return se


def send_admin_email(subject, body_template, body_context):
    """
    Send an admin email and don't log it
    """
    body_context_modified = body_context.copy()
    body_context_modified['BASE_URL'] = BASE_URL

    # Generate html body
    html_body = render_to_string('emails/admin/'+body_template, body_context_modified)

    if EMAIL_DEV_PREFIX:
        subject += ' [DEV]'

    pm_dict = {
            'sender': POSTMARK_SENDER,
            'to': ','.join([x[1] for x in ADMINS]),
            'subject': subject,
            'html_body': html_body,
            }

    # Make email object
    pm = PMMail(**pm_dict)

    # Send email object (no logging)
    return pm.send()
