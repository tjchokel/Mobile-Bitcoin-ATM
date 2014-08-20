import re
import random
import urlparse

from urllib import urlencode

import phonenumbers
from django import forms
from django.utils.translation import ugettext_lazy as _

SATOSHIS_PER_BTC = 10**8
SATOSHIS_PER_MILLIBITCOIN = 10**5
STANDARD_TX_FEE_IN_SATOSHIS = 10**4


def satoshis_to_btc(satoshis):
    # invertible, ugly for printing
    return satoshis / float(SATOSHIS_PER_BTC)


def satoshis_to_mbtc(satoshis):
    # invertible, ugly for printing
    return satoshis / float(SATOSHIS_PER_MILLIBITCOIN)


def mbtc_to_satoshis(mbtc):
    # invertible, ugly for printing
    return mbtc * SATOSHIS_PER_MILLIBITCOIN


def btc_to_satoshis(btc):
    # invertible, ugly for printing
    return long(float(btc) * SATOSHIS_PER_BTC)


def format_num_for_printing(num, decimals):
    " comma separates thousands, rounds to decimal, gets rid of trailing 0s"

    # returns returns something like '{0:,.5f}'
    format_string = '{0:,.%sf}' % decimals

    # returns something like 123,456.78910
    return_string = format_string.format(num)

    # Hack to get rid of any trailing decimals
    return return_string.rstrip('0').rstrip('.')


def format_btc(btc):
    return format_num_for_printing(btc, 9)


def format_btc_rounded(btc):
    return format_num_for_printing(btc, 2)


def format_mbtc(mbtc):
    return format_num_for_printing(mbtc, 6)


def format_mbtc_rounded(mbtc):
    return format_num_for_printing(mbtc, 2)


def format_fiat_amount(amount, currency_symbol, currency_code=None):
    """
    Utility function for printing
    """
    if amount > 10000:
        # No decimal places for large numbers
        amount_formatted = '%s' % '{:,.0f}'.format(round(amount, 0))
    else:
        amount_formatted = '%s' % '{:,.2f}'.format(amount)

    if currency_code:
        return "%s%s %s" % (currency_symbol, amount_formatted, currency_code)
    else:
        return "%s%s" % (currency_symbol, amount_formatted)


def format_satoshis_with_units(satoshis):
    '''
    Great function for displaying to user (BTC or mBTC, which makes more sense)
    Not invertible
    '''
    if satoshis >= SATOSHIS_PER_BTC:
        return '%s BTC' % format_btc(satoshis_to_btc(satoshis))
    else:
        return '%s mBTC' % format_mbtc(satoshis_to_mbtc(satoshis))


def format_satoshis_with_units_rounded(satoshis):
    '''
    Great function for displaying to user (BTC or mBTC, which makes more sense)
    Not invertible
    '''
    if satoshis >= SATOSHIS_PER_BTC:
        return '%s BTC' % format_btc_rounded(satoshis_to_btc(satoshis))
    else:
        return '%s mBTC' % format_mbtc_rounded(satoshis_to_mbtc(satoshis))


def get_client_ip(request):
    """
    Get IP from a request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def cat_email_header(name, email):
    assert '@' in email, email
    if name:
        return '%s <%s>' % (name, email)
    return email


def split_email_header(header):
    if '<' in header and '>' in header:
        name, email = re.findall('(.*)<(.*)>', header)[0]
    else:
        name = None
        email = header
    assert '@' in email
    return name, email


def uri_to_url(base_url, uri):
    """
    Take a URI and map it a URL:
    /foo -> http://coinsafe.com/foo
    """
    if not uri:
        return base_url
    if uri.startswith('/'):
        return '%s%s' % (base_url, uri)
    return '%s/%s' % (base_url, uri)


def get_file_ext(fname):
    """
    Ex:
      `foo.jpg` -> `ppt`
      `foo` -> `` (no file extension, this shouldn't happen though)

    See unit tests for more extreme edge cases
    Will never return None for safety, returns empty string instead.
    """

    if '.' not in fname:
        return ''

    split_result = fname.lower().split('.')
    if len(split_result) == 1:
        if fname.startswith('.'):
            # edge case of `.jpg` is the full filename
            return split_result[0]
        return ''
    return split_result[-1]


def simple_random_generator(num_chars=32, eligible_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'):

    """
    Generate a random password using the characters in `chars` and with a
    length of `size`.

    http://stackoverflow.com/a/2257449

    Not cryptographically secure but works on all OSs without blocking.
    """
    return ''.join(random.SystemRandom().choice(eligible_chars) for x in range(num_chars))


def simple_csprng(num_chars=32, eligible_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ23456789'):

    """
    Generate a random password using the characters in `chars` and with a
    length of `size`.

    http://stackoverflow.com/a/2257449

    Cryptographically secure but may not work on all OSs.
    Shouldn't cause blocking but it's possible.
    """
    return ''.join(random.SystemRandom().choice(eligible_chars) for x in range(num_chars))


def clean_phone_num(self):
    """
    Helper function for cleaning phone numbers (that may just be a country code)

    Phone Number field must be called `phone_num`

    Kept in utils.py so it can be in only one place and called from everywhere.
    """
    # TODO: restrict phone number to one of Plivo's serviced countries:
    # https://s3.amazonaws.com/mf-tmp/plivo_countries.txt
    phone_num = self.cleaned_data['phone_num']
    if not phone_num or len(phone_num.strip('+').strip()) < 4:
        return None
    try:
        pn_parsed = phonenumbers.parse(phone_num, None)
        if not phonenumbers.is_valid_number(pn_parsed):
            err_msg = _("Sorry, that number isn't valid")
            raise forms.ValidationError(err_msg)
    except phonenumbers.NumberParseException:
        err_msg = _("Sorry, that number doesn't look like a real number")
        raise forms.ValidationError(err_msg)
    return phone_num


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
