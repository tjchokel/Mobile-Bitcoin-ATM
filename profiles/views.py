from django.shortcuts import get_object_or_404

from annoying.decorators import render_to

from profiles.models import ShortURL
from bitcoins.models import BTCTransaction

import math


@render_to('profiles/main.html')
def merchant_site(request, uri):
    short_url_obj = get_object_or_404(ShortURL, uri_lowercase=uri.lower(), deleted_at=None)
    merchant = short_url_obj.merchant
    
    market_price = BTCTransaction.get_btc_market_price(merchant.currency_code)
    
    cashin_fee = market_price * merchant.get_cashin_percent_markup() / 100.00
    cashout_fee = market_price * merchant.get_cashout_percent_markup() / 100.00
    
    cashin_price = math.floor((market_price + cashin_fee)*100)/100.00
    cashout_price = math.floor((market_price - cashout_fee)*100)/100.00

    currency_symbol = merchant.get_currency_symbol()

    cashin_price_formatted = '%s%s' % (currency_symbol, cashin_price)
    cashout_price_formatted = '%s%s' % (currency_symbol, cashout_price)

    return {'merchant': short_url_obj.merchant, 'cashin_price': cashin_price_formatted, 'cashout_price': cashout_price_formatted}
