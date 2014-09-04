
def credential_status(request):

    has_cred = False
    cred_appears_usable = None
    cred_appears_funded = False

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
                        cred_appears_funded = True

    return {
            'has_cred': has_cred,
            'cred_appears_usable': cred_appears_usable,
            'cred_appears_funded': cred_appears_funded,
            }
