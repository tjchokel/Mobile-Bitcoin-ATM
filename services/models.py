from django.db import models

from jsonfield import JSONField


class APICall(models.Model):
    """
    To keep track of all our external API calls and aid in debugging as well.

    TODO: Deal with security implications with data being passed in here
    """

    # api_name choices
    BCI_RECIEVE_PAYMENTS = 'BRP'
    BCI_TXN_FROM_HASH = 'BTH'
    BCI_TXN_FROM_ADDR = 'BTA'
    API_NAME_CHOICES = (
            (BCI_RECIEVE_PAYMENTS, 'blockchain.info recieve payments API'),
            (BCI_TXN_FROM_HASH, 'blockchain.info txn data from hash'),
            (BCI_TXN_FROM_ADDR, 'blockchain.info txn data from address'),
            )

    # Main fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    api_name = models.CharField(choices=API_NAME_CHOICES, max_length=3,
            null=False, blank=False, db_index=True)
    url_hit = models.URLField(blank=False, null=False, db_index=True)
    response_code = models.PositiveSmallIntegerField(blank=False, null=False,
            db_index=True)
    post_params = JSONField(blank=True, null=True)
    headers = models.CharField(max_length=2048, null=True, blank=True)
    api_results = models.CharField(max_length=100000, blank=True, null=True)

    # optional FK
    user = models.ForeignKey('business.AppUser', null=True, blank=True)
