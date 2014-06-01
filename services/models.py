from django.db import models

from jsonfield import JSONField

from utils import get_client_ip


class APICall(models.Model):
    """
    To keep track of all our external API calls and aid in debugging as well.

    TODO: deal with security implications with data being passed in here
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
    user = models.ForeignKey('merchants.AppUser', null=True, blank=True)


class WebHook(models.Model):
    """
    To keep track of all our webhooks and aid in debugging as well.

    TODO: deal with security implications with data being passed in here
    """

    # api_name choices
    BCI_PAYMENT_FORWARDED = 'BPF'
    BLOCKCYPHER_TX_MONITORING = 'BTM'
    API_NAME_CHOICES = (
            (BCI_PAYMENT_FORWARDED, 'blockchain.info payment forwarded'),
            (BLOCKCYPHER_TX_MONITORING, 'blockcypher transaction monitoring'),
            )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    # IP and UA of machine hitting coinsafe
    ip_address = models.IPAddressField(null=False, blank=False, db_index=True)
    user_agent = models.CharField(max_length=1024, blank=True, db_index=True)
    api_name = models.CharField(choices=API_NAME_CHOICES, max_length=3,
            null=False, blank=False, db_index=True)
    hostname = models.CharField(max_length=512, blank=False, null=False, db_index=True)
    request_path = models.CharField(max_length=2048, blank=False, null=False, db_index=True)
    uses_https = models.BooleanField(db_index=True)
    data_from_get = JSONField(blank=True, null=True)
    data_from_post = JSONField(blank=True, null=True)

    def __str__(self):
        return '%s from %s' % (self.id, self.api_name)

    @classmethod
    def create_webhook(cls, request, api_name):
        return WebHook.objects.create(
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                api_name=api_name,
                hostname=request.get_host(),
                request_path=request.path,
                uses_https=request.is_secure(),
                data_from_get=request.GET,
                data_from_post=request.POST,
                )
