import re
import random

SATOSHIS_PER_BTC = 10**8
SATOSHIS_PER_MILLIBITCOIN = 10**5
CAPITAL_CONTROL_COUNTRIES = ['ARS', 'VEF']


def satoshis_to_btc(satoshis):
    # invertible, ugly for printing
    return satoshis / float(SATOSHIS_PER_BTC)


def satoshis_to_mbtc(satoshis):
    # invertible, ugly for printing
    return satoshis / float(SATOSHIS_PER_MILLIBITCOIN)


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


def format_mbtc(mbtc):
    return format_num_for_printing(mbtc, 6)


def format_satoshis_with_units(satoshis):
    '''
    Great function for displaying to user (BTC or mBTC, which makes more sense)
    Not invertible
    '''
    if satoshis >= SATOSHIS_PER_BTC:
        return '%s BTC' % format_btc(satoshis_to_btc(satoshis))
    else:
        return '%s mBTC' % format_mbtc(satoshis_to_mbtc(satoshis))


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

    Note: this is NOT a CSPRNG and shouldn't be used for crypto.

    http://stackoverflow.com/a/2257449
    """
    #FIXME: switch to CSPRNG
    return ''.join(random.choice(eligible_chars) for x in range(num_chars))
