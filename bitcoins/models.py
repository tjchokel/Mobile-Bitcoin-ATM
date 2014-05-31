from django.db import models


class BTCAddress(models.Model):
    """
    CoinSafe BTC Address

    NEVER any private keys here.
    """
    generated_at = models.DateTimeField(blank=False, null=False, db_index=True)
    b58_address = models.CharField(blank=False, null=False, max_length=34,
            db_index=True, unique=True)
    revealed_to_user_at = models.DateTimeField(blank=True, null=True,
            db_index=True)
    retired_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # This could be triggered from polling (pull) or push notifications
    last_checked_at = models.DateTimeField(blank=True, null=True,
            db_index=True)
    business = models.ForeignKey('business.Business', blank=True, null=True)

    def get_transaction(self):
        return self.btctransaction_set.last()

    def get_all_transactions(self):
        return self.btctransaction_set.all()

    def get_current_shopper(self):
        return self.shopper_set.last()


class BTCTransaction(models.Model):
    """
    Only transactions that affect our users.
    Both deposits and withdrawals.
    """
    added_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # TODO: solve transaction malleability issue
    txn_hash = models.CharField(
        max_length=64, blank=True, null=True, unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=True, null=True, db_index=True)
    conf_num = models.PositiveSmallIntegerField(
        blank=True, null=True, db_index=True)
    irreversible_by = models.DateTimeField(
        blank=True, null=True, db_index=True)
    suspected_double_spend_at = models.DateTimeField(
        blank=True, null=True, db_index=True)
    btc_address = models.ForeignKey(BTCAddress, blank=True, null=True)
    fiat_ammount = models.DecimalField(
        blank=True, null=True, max_digits=5, decimal_places=2)

    def received_new_confirmation(self):
        # TODO: make this actually work
        return True

    def reached_confirmation_threshold(self):
        # TODO: make this actually do this
        if self.conf_num > 0:
            return True
        return False
