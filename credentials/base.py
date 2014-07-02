

class BaseCredential:

    def __init__(self, cred):
        self.cred = cred

    def __str__(self):
        return '%s for %s from %s' % (self.cred.id,
                self.cred.get_credential_type_display(),
                self.cred.merchant.business_name)

    def get_balance(self):
        raise Exception('Not Implemented')

    def request_cashout(self):
        raise Exception('Not Implemented')

    def send_btc(self):
        raise Exception('Not Implemented')

    def get_receiving_address(self):
        raise Exception('Not Implemented')

    def get_new_receiving_address(self):
        raise Exception('Not Implemented')


class BaseSellOrder:

    def __init__(self, cred):
        self.cred = cred

    def __str__(self):
        return '%s: %s' % (self.cred.id, self.cred.created_at)
