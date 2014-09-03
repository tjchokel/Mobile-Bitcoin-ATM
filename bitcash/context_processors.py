
def credential_status(request):

    has_cred = False
    cred_appears_usable = None

    user = request.user
    if user.is_authenticated():
        merchant = user.get_merchant()
        if merchant:
            credential = merchant.get_lastest_api_credential()
            if credential:
                has_cred = True
                cred_appears_usable = credential.appears_usable()

    return {'has_cred': has_cred, 'cred_appears_usable': cred_appears_usable}
