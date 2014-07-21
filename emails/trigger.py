from django.template.loader import render_to_string

from bitcash.settings import POSTMARK_SENDER, EMAIL_DEV_PREFIX, BASE_URL

from utils import split_email_header, cat_email_header

from postmark import PMMail

import re
import urlparse
from urllib import urlencode


def add_qs(link, qs_dict=None):
    """
    Add a querystring dict to a link:

    link = 'http://example.com/directory/page.html'
    qs = {'email': 'foo@bar.com'}

    ->

    http://example.com/directory/page.html?email=foo@bar.com

    """

    s = urlparse.urlsplit(link)

    existing_qs_dict = urlparse.parse_qs(s.query)
    qs_dict.update(existing_qs_dict)

    query = urlencode(qs_dict)
    return urlparse.urlunsplit((s.scheme, s.netloc, s.path, query, s.fragment))


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


# TODO: create non-blocking queue system and move email sending to queue
def send_and_log(subject, body_template, to_merchant=None, to_email=None,
        to_name=None, body_context={}, from_name=None,
        from_email=None, cc_name=None, cc_email=None):
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
            to_name = to_merchant.business_name

        # append ?e=email to all links in email
        html_body = append_qs(
                html=html_body,
                qs_dict={'e': to_merchant.user.email},
                link_text=BASE_URL,
                )

    if EMAIL_DEV_PREFIX:
        subject += ' [DEV]'

    # BCC everything to self (for now at least)
    pm_dict = {
            'sender': cat_email_header(from_name, from_email),
            'to': cat_email_header(to_name, to_email),
            'bcc': POSTMARK_SENDER,
            'subject': subject,
            'html_body': html_body,
            }

    if cc_email:
        pm_dict['cc'] = cat_email_header(cc_name, cc_email)

    # Make email object
    pm = PMMail(**pm_dict)

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
            subject=subject)

    # Send email object
    pm.send()

    return se
