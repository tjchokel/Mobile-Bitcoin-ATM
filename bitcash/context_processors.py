
def credential_status(request):

    has_cred = False
    cred_appears_usable = None
    appears_to_have_btc = False

    user = request.user
    if user.is_authenticated():
        merchant = user.get_merchant()
        if merchant:
            credential = merchant.get_latest_api_credential()
            if credential:
                has_cred = True
                cred_appears_usable = credential.appears_usable()
                latest_balance = credential.get_latest_balance()
                if latest_balance:
                    if latest_balance.satoshis > 0:
                        appears_to_have_btc = True

    return {
            'has_cred': has_cred,
            'cred_appears_usable': cred_appears_usable,
            'appears_to_have_btc': appears_to_have_btc,
            }
