from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from emails.trigger import send_and_log

from phonenumber_field.modelfields import PhoneNumberField

from utils import get_client_ip, simple_csprng
from countries import ALL_COUNTRIES

from datetime import timedelta


AbstractUser._meta.get_field_by_name('username')[0].max_length = 100
AbstractUser._meta.get_field('username').validators[0].limit_value = 100


class AuthUser(AbstractUser):
    """
    Right now this is just merchants but it can support cashiers, shoppers,
    owners with multiple merchants and all types of things in the future.

    http://qr.ae/svQjw
    """
    full_name = models.CharField(max_length=60, blank=True,
            null=True, db_index=True)
    phone_num = PhoneNumberField(blank=True, null=True, db_index=True)
    phone_num_country = models.CharField(
        max_length=256, blank=True, null=True, db_index=True)

    def get_merchant(self):
        return self.merchant_set.last()

    def get_login_uri(self):
        return '%s?e=%s' % (reverse('login_request'), self.email)

    def create_email_auth_token(self, request):
        return EmailAuthToken.objects.create(
                auth_user=self,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                )


class LoggedLogin(models.Model):
    login_at = models.DateTimeField(auto_now_add=True, db_index=True)
    auth_user = models.ForeignKey(AuthUser, blank=False, null=False)
    ip_address = models.IPAddressField(null=False, blank=False, db_index=True)
    user_agent = models.CharField(max_length=1024, blank=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.ip_address)

    @classmethod
    def record_login(cls, request):
        return cls.objects.create(
                auth_user=request.user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT'),
                )


class FutureShopper(models.Model):
    """
    Customer that signed up to be notified when merchants are in their area
    """
    email = models.EmailField(blank=False, null=False, db_index=True)
    city = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    country = models.CharField(max_length=256, blank=False, null=False, db_index=True, choices=ALL_COUNTRIES)
    intention = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    message = models.CharField(max_length=5000, blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.email)


def default_expires_time():
    return now() + timedelta(hours=24)


class EmailAuthToken(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    auth_user = models.ForeignKey(AuthUser, blank=False, null=False)
    ip_address = models.IPAddressField(null=False, blank=False, db_index=True)
    user_agent = models.CharField(max_length=1024, blank=False)
    verif_key = models.CharField(max_length=64, db_index=True, default=simple_csprng, blank=False, null=False)
    key_used_at = models.DateTimeField(default=None, null=True, blank=True, db_index=True)
    key_expires_at = models.DateTimeField(default=default_expires_time, null=False, blank=False, db_index=True)
    key_deleted_at = models.DateTimeField(default=default_expires_time, null=True, blank=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.verif_key)

    def get_reset_pw_uri(self):
        return reverse('reset_password', kwargs={'verif_key': self.verif_key})

    def send_pwreset_email(self):
        """
        Send password reset email to merchant.
        May require small changes for users generally.
        """
        auth_user = self.auth_user
        body_context = {'pw_reset_uri': self.get_reset_pw_uri()}
        return send_and_log(
                subject='CoinSafe Password Reset for %s' % auth_user.full_name,
                body_template='user/password_reset.html',
                to_merchant=auth_user.get_merchant(),
                body_context=body_context,
                )

    @classmethod
    def expire_outstanding_tokens(cls, self):
        for unexpired_token in cls.objects.filter(key_deleted_at=None, auth_user=self.auth_user):
            unexpired_token.key_deleted_at = now()
            unexpired_token.save()
