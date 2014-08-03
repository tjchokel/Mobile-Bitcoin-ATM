from django.db import models
from django.core.urlresolvers import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext as _

from annoying.functions import get_object_or_None

from bitcoins.bci import set_bci_webhook
from bitcoins.blockcypher import set_blockcypher_webhook

from emails.trigger import send_and_log

from phones.models import SentSMS
from emails.models import SentEmail

from countries import BFHCurrenciesList

from bitcash.settings import BASE_URL, CAPITAL_CONTROL_COUNTRIES

from utils import (uri_to_url, simple_random_generator, satoshis_to_btc,
        satoshis_to_mbtc, format_mbtc, format_satoshis_with_units,
        format_num_for_printing, btc_to_satoshis)

import datetime
import json
import requests

from decimal import Decimal


class DestinationAddress(models.Model):
    """
    What's uploaded by the user.
    """
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    b58_address = models.CharField(blank=False, null=False, max_length=34, db_index=True)
    retired_at = models.DateTimeField(blank=True, null=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    credential = models.ForeignKey('credentials.BaseCredential', blank=True, null=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.b58_address)

    def create_new_forwarding_address(self):

        # generate random id so that each webhook has a unqiue endpoint to hit
        # this helps solve some edge cases
        kw_to_use = {'random_id': simple_random_generator(16)}

        # blockchain.info and blockcypher callback uris
        bci_uri = reverse('process_bci_webhook', kwargs=kw_to_use)
        blockcypher_uri = reverse('process_blockcypher_webhook', kwargs=kw_to_use)

        # get address to forward to (this also signs up for webhook on destination address)
        forwarding_address = set_bci_webhook(
                dest_address=self.b58_address,
                callback_url=uri_to_url(BASE_URL, bci_uri),
                merchant=self.merchant)

        # Store it in the DB
        ForwardingAddress.objects.create(
                b58_address=forwarding_address,
                destination_address=self,
                merchant=self.merchant)

        # set webhook for forwarding address
        set_blockcypher_webhook(
                monitoring_address=forwarding_address,
                callback_url=uri_to_url(BASE_URL, blockcypher_uri),
                merchant=self.merchant)

        return forwarding_address


class ForwardingAddress(models.Model):
    """
    One-time receiving address generated by blockchain.info
    """
    generated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    b58_address = models.CharField(blank=False, null=False, max_length=34,
            db_index=True, unique=True)
    paid_out_at = models.DateTimeField(blank=True, null=True, db_index=True)
    destination_address = models.ForeignKey(DestinationAddress, blank=False, null=False)

    # technically, this is redundant through DestinationAddress
    # but having it here makes for easier querying (especially before there is a destination address)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    shopper = models.ForeignKey('shoppers.Shopper', blank=True, null=True)
    customer_confirmed_deposit_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.b58_address)

    def get_transaction(self):
        return self.btctransaction_set.last()

    def get_confs_needed(self):
        return self.merchant.minimum_confirmations

    def get_all_forwarding_transactions(self):
        return self.btctransaction_set.filter(destination_address__isnull=True).order_by('-id')

    def get_first_forwarding_transaction(self):
        forwarding_txns = self.get_all_forwarding_transactions()
        if forwarding_txns:
            return forwarding_txns[0]
        return None

    def get_and_group_all_transactions(self):
        " Get forwarding and destination transactions grouped by txn pair "

        txn_group_list = []

        for dest_txn in self.btctransaction_set.filter(destination_address__isnull=False):
            txn_dict = {
                    'satoshis': dest_txn.satoshis,
                    'destination_txn_hash': dest_txn.txn_hash,
                    'destination_conf_num': dest_txn.conf_num,
                    }

            fwd_txn = dest_txn.input_btc_transaction
            if fwd_txn:
                txn_dict['forwarding_txn_hash'] = fwd_txn.txn_hash
                txn_dict['forwarding_conf_num'] = fwd_txn.conf_num
                txn_dict['forwarding_fiat_amount'] = fwd_txn.fiat_amount
                txn_dict['currency_code_when_created'] = fwd_txn.currency_code_when_created

            # add txn to list
            txn_group_list.append(txn_dict)

        fwd_txn_hashes = [x['forwarding_txn_hash'] for x in txn_group_list if 'forwarding_txn_hash' in x]

        # loop through forwarding txns to get any that might be missing (no destination confirms)
        for fwd_txn in self.btctransaction_set.filter(destination_address__isnull=True):
            if fwd_txn.txn_hash not in fwd_txn_hashes:
                txn_dict = {
                        'satoshis': fwd_txn.satoshis,
                        'forwarding_txn_hash': fwd_txn.txn_hash,
                        'forwarding_conf_num': fwd_txn.conf_num,
                        'forwarding_fiat_amount': fwd_txn.fiat_amount,
                        'currency_code_when_created': fwd_txn.currency_code_when_created,
                        }
                txn_group_list.append(txn_dict)

        return txn_group_list

    def all_transactions_complete(self):
        transactions = self.btctransaction_set.filter(destination_address__isnull=True)
        incomplete_transactions = transactions.filter(met_minimum_confirmation_at__isnull=True)
        return (transactions.count() > 0 and incomplete_transactions.count() == 0)

    def get_satoshis_and_fiat_transactions_total(self):
        transactions = self.get_all_forwarding_transactions()
        satoshis, fiat = 0, 0
        for txn in transactions:
            if txn.met_minimum_confirmation_at:
                satoshis += txn.satoshis
                fiat += txn.fiat_amount
        return satoshis, fiat

    def get_satoshis_transactions_total(self):
        return self.get_satoshis_and_fiat_transactions_total()[0]

    def get_btc_transactions_total_formatted(self):
        return format_satoshis_with_units(self.get_satoshis_transactions_total())

    def get_fiat_transactions_total(self):
        return self.get_satoshis_and_fiat_transactions_total()[1]

    def get_fiat_transactions_total_formatted(self):
        ' Assumes that all deposits to a forwarding address use the same currency '
        return '%s%s %s' % (self.merchant.get_currency_symbol(),
                self.get_fiat_transactions_total(),
                self.get_first_forwarding_transaction().currency_code_when_created)

    # If an address has already been shown to the user, can it be shown again
    def can_be_reused(self):
        seconds_old = (now() - self.generated_at).total_seconds()
        if seconds_old > 600:
            return False
        if self.customer_confirmed_deposit_at:
            return False
        if self.get_transaction():
            return False
        return True


class BTCTransaction(models.Model):
    """
    Transactions that affect our users.

    Both ForwardingAddress txn (initial send) and DestinationAddress txn
    (relay) are tracked separately in this same model.
    """
    added_at = models.DateTimeField(auto_now_add=True, db_index=True)
    txn_hash = models.CharField(max_length=64, blank=False, null=False, unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=True, null=True, db_index=True)
    conf_num = models.PositiveSmallIntegerField(blank=False, null=False, db_index=True)
    irreversible_by = models.DateTimeField(blank=True, null=True, db_index=True)
    suspected_double_spend_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # We always have this for deposits:
    forwarding_address = models.ForeignKey(ForwardingAddress, blank=True, null=True)
    # We we only have this when the deposit is being relayed:
    destination_address = models.ForeignKey(DestinationAddress, blank=True, null=True)
    # We only have this once the deposit has been relayed (and assuming all APIS worked as expected)
    input_btc_transaction = models.ForeignKey('self', blank=True, null=True)
    fiat_amount = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    currency_code_when_created = models.CharField(max_length=5, blank=True, null=True, db_index=True)
    met_minimum_confirmation_at = models.DateTimeField(blank=True, null=True, db_index=True)
    min_confirmations_overrode_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.txn_hash)

    def get_merchant(self):
        return self.forwarding_address.merchant

    def get_shopper(self):
        return self.forwarding_address.shopper

    def set_merchant_confirmation_override(self):
        self.min_confirmations_overrode_at = now()
        self.met_minimum_confirmation_at = now()
        self.save()

    @classmethod
    def get_forwarding_txns(cls, self):
        ''' Will include self if self is a forwarding txn '''
        return cls.objects.filter(
                forwarding_address=self.forwarding_address,
                destination_address=None)

    def get_destination_txns(self):
        ''' Will include self if self is a destination txn '''
        return BTCTransaction.objects.filter(
                forwarding_address=self.forwarding_address,
                destination_address__isnull=False)

    def calculate_exchange_rate(self):
        return format_num_for_printing(float(self.fiat_amount) / satoshis_to_btc(self.satoshis), 2)

    def get_exchange_rate_formatted(self):
        return '%s%s %s' % (
                self.get_currency_symbol(),
                self.calculate_exchange_rate(),
                self.currency_code_when_created
                )

    def get_status(self):
        if self.forwarding_address.paid_out_at:
            return _('Cash Paid Out')
        if self.met_minimum_confirmation_at:
            return _('BTC Received')
        else:
            msg = 'BTC Pending (%s of %s Confirms Needed)' % (
                    self.conf_num,
                    self.get_confs_needed(),
                    )
            return _(msg)

    def get_currency_symbol(self):
        if self.currency_code_when_created:
            return BFHCurrenciesList[self.currency_code_when_created]['symbol'].decode('utf-8')
        else:
            return '$'

    def format_mbtc_amount(self):
        return format_mbtc(satoshis_to_mbtc(self.satoshis))

    def format_satoshis_amount(self):
        return format_satoshis_with_units(self.satoshis)

    def get_confs_needed(self):
        return self.get_merchant().minimum_confirmations

    def meets_minimum_confirmations(self):
        return (self.conf_num >= self.get_confs_needed())

    def get_fiat_amount_formatted(self):
        return '%s%s %s' % (self.get_currency_symbol(), self.fiat_amount,
                self.currency_code_when_created)

    def get_time_range_in_minutes(self):
        additional_confs_needed = self.get_total_confirmations_required() - self.conf_num
        min_time = 10 * additional_confs_needed
        max_time = 20 * additional_confs_needed
        return '%s-%s' % (min_time, max_time)

    def get_total_confirmations_required(self):
        return self.get_merchant().minimum_confirmations

    def send_shopper_newtx_email(self, force_resend=False):

        BODY_TEMPLATE = 'shopper/cashout_newtx.html'
        existing_newtx_email = get_object_or_None(SentEmail,
                btc_transaction=self, body_template=BODY_TEMPLATE)

        existing_confirmedtx_email = get_object_or_None(SentEmail,
                btc_transaction=self,
                body_template='shopper/cashout_txconfirmed.html')

        if existing_newtx_email or existing_confirmedtx_email:
            if not force_resend:
                # Protection against double-sending
                return

        shopper = self.get_shopper()
        if shopper and shopper.email:
            merchant = self.get_merchant()
            satoshis_formatted = self.format_satoshis_amount()
            body_context = {
                    'salutation': shopper.name,
                    'satoshis_formatted': satoshis_formatted,
                    'merchant_name': merchant.business_name,
                    'exchange_rate_formatted': self.get_exchange_rate_formatted(),
                    'fiat_amount_formatted': self.get_fiat_amount_formatted(),
                    'time_range_in_minutes': self.get_time_range_in_minutes(),
                    'confirmations_needed': merchant.minimum_confirmations,
                    'notification_methods_formatted': shopper.get_notification_methods_formatted(),
                    'tx_hash': self.txn_hash,
                    }
            return send_and_log(
                    subject='%s Sent' % satoshis_formatted,
                    body_template=BODY_TEMPLATE,
                    to_merchant=None,
                    to_email=shopper.email,
                    to_name=shopper.name,
                    body_context=body_context,
                    btc_transaction=self,
                    )

    def send_shopper_newtx_sms(self, force_resend=False):

        existing_newtx_sms = get_object_or_None(SentSMS, btc_transaction=self, message_type=SentSMS.SHOPPER_NEW_TX)
        existing_confirmedtx_sms = get_object_or_None(SentSMS, btc_transaction=self, message_type=SentSMS.SHOPPER_TX_CONFIRMED)

        if existing_newtx_sms or existing_confirmedtx_sms:
            if not force_resend:
                # Protection against double-sending
                return

        shopper = self.get_shopper()
        if shopper and shopper.phone_num:
            msg = 'You just sent %s to %s. '
            msg += 'You will receive %s when this transaction confirms in %s mins.'
            msg = msg % (
                    self.format_satoshis_amount(),
                    self.get_merchant().business_name,
                    self.get_fiat_amount_formatted(),
                    self.get_time_range_in_minutes()
                    )
            msg = _(msg)
            return SentSMS.send_and_log(
                    phone_num=shopper.phone_num,
                    message=msg,
                    to_user=None,
                    to_merchant=None,
                    to_shopper=shopper,
                    message_type=SentSMS.SHOPPER_NEW_TX,
                    btc_transaction=self,
                    )

    def send_shopper_txconfirmed_email(self, force_resend=False):

        BODY_TEMPLATE = 'shopper/cashout_txconfirmed.html'
        if get_object_or_None(SentEmail, btc_transaction=self, body_template=BODY_TEMPLATE):
            if not force_resend:
                # Protection against double-sending
                return

        shopper = self.get_shopper()
        if shopper and shopper.email:
            merchant = self.get_merchant()
            satoshis_formatted = self.format_satoshis_amount()
            body_context = {
                    'salutation': shopper.name,
                    'satoshis_formatted': satoshis_formatted,
                    'merchant_name': merchant.business_name,
                    'exchange_rate_formatted': self.get_exchange_rate_formatted(),
                    'fiat_amount_formatted': self.get_fiat_amount_formatted(),
                    'tx_hash': self.txn_hash,
                    'review_link': '',
                    }
            return send_and_log(
                    subject='%s Confirmed' % satoshis_formatted,
                    body_template=BODY_TEMPLATE,
                    to_merchant=None,
                    to_email=shopper.email,
                    to_name=shopper.name,
                    body_context=body_context,
                    btc_transaction=self,
                    )

    def send_shopper_txconfirmed_sms(self, force_resend=False):

        if get_object_or_None(SentSMS, btc_transaction=self, message_type=SentSMS.SHOPPER_TX_CONFIRMED):
            if not force_resend:
                # Protection against double-sending
                return

        shopper = self.get_shopper()
        if shopper and shopper.phone_num:
            msg = 'The %s you sent to %s has been confirmed. They now owe you %s.'
            msg = msg % (
                    self.format_satoshis_amount(),
                    self.get_merchant().business_name,
                    self.get_fiat_amount_formatted(),
                    )
            msg = _(msg)
            return SentSMS.send_and_log(
                    phone_num=shopper.phone_num,
                    message=msg,
                    to_user=None,
                    to_merchant=None,
                    to_shopper=shopper,
                    message_type=SentSMS.SHOPPER_TX_CONFIRMED,
                    btc_transaction=self,
                    )

    def send_merchant_txconfirmed_email(self, force_resend=False):
        # TODO: allow for notification settings

        BODY_TEMPLATE = 'merchant/shopper_cashout.html'
        if get_object_or_None(SentEmail, btc_transaction=self, body_template=BODY_TEMPLATE):
            if not force_resend:
                # Protection against double-sending
                return

        merchant = self.get_merchant()
        shopper = self.get_shopper()
        satoshis_formatted = self.format_satoshis_amount()
        body_context = {
                'satoshis_formatted': satoshis_formatted,
                'exchange_rate_formatted': self.get_exchange_rate_formatted(),
                'fiat_amount_formatted': self.get_fiat_amount_formatted(),
                'tx_hash': self.txn_hash,
                'coinsafe_tx_uri': reverse('merchant_transactions'),
                }
        subject = '%s Received' % satoshis_formatted
        if shopper and shopper.name:
            subject += 'from %s' % shopper.name
            body_context['shopper_name'] = shopper.name
        return send_and_log(
                body_template=BODY_TEMPLATE,
                subject='%s Received' % satoshis_formatted,
                to_merchant=merchant,
                body_context=body_context,
                btc_transaction=self,
                )

    def send_merchant_txconfirmed_sms(self, force_resend=False):
        # TODO: allow for notification settings

        if get_object_or_None(SentSMS, btc_transaction=self, message_type=SentSMS.MERCHANT_TX_CONFIRMED):
            if not force_resend:
                # Protection against double-sending
                return

        merchant = self.get_merchant()
        if merchant.phone_num:
            msg = 'The %s you received from %s has been confirmed. Please pay them %s immediately.'
            shopper = self.get_shopper()
            if shopper and shopper.name:
                customer_string = shopper.name
            else:
                customer_string = 'the customer'
            msg = msg % (
                    self.format_satoshis_amount(),
                    customer_string,
                    self.get_fiat_amount_formatted(),
                    )
            msg = _(msg)
            return SentSMS.send_and_log(
                    phone_num=merchant.phone_num,
                    message=msg,
                    to_user=merchant.user,
                    to_merchant=merchant,
                    to_shopper=shopper,
                    message_type=SentSMS.MERCHANT_TX_CONFIRMED,
                    btc_transaction=self,
                    )

    def send_all_txconfirmed_notifications(self, force_resend=False):
        """
        Send out all notifications, and continue to the next one in the event of an error.

        TODO: better logging for these edge cases

        """
        try:
            self.send_merchant_txconfirmed_email(force_resend=False)
        except Exception as e:
            print 'Error was: %s' % e
        try:
            self.send_merchant_txconfirmed_sms(force_resend=False)
        except Exception as e:
            print 'Error was: %s' % e
        try:
            self.send_shopper_txconfirmed_email(force_resend=False)
        except Exception as e:
            print 'Error was: %s' % e
        try:
            self.send_shopper_txconfirmed_sms(force_resend=False)
        except Exception as e:
            print 'Error was: %s' % e

    def send_all_newtx_notifications(self, force_resend=False):
        """
        Send out all notifications, and continue to the next one in the event of an error.

        TODO: better logging for these edge cases

        """
        try:
            self.send_shopper_newtx_email(force_resend=False)
        except Exception as e:
            print 'Error was: %s' % e
        try:
            self.send_shopper_newtx_sms(force_resend=False)
        except Exception as e:
            print 'Error was: %s' % e

    def get_type(self):
        return _('Bought BTC')

    @staticmethod
    def get_btc_price(currency_code):
        if currency_code in CAPITAL_CONTROL_COUNTRIES:
            url = 'https://conectabitcoin.com/en/market_prices.json'
            r = requests.get(url)
            content = json.loads(r.content)
            key = 'btc_'+currency_code.lower()
            return content[key]['sell']
        else:
            url = 'https://api.bitcoinaverage.com/ticker/global/'+currency_code
            r = requests.get(url)
            content = json.loads(r.content)
            return content['last']


class ShopperBTCPurchaseManager(models.Manager):
    def active(self, *args, **kwargs):
        """
        Addresses that have been revealed to users
        """
        return super(ShopperBTCPurchaseManager, self).get_query_set().filter(
                cancelled_at=None, *args, **kwargs).order_by('-added_at')


class ShopperBTCPurchase(models.Model):
    """
    Model for bitcoin purchase (cash in) request
    """

    added_at = models.DateTimeField(auto_now_add=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    shopper = models.ForeignKey('shoppers.Shopper', blank=False, null=False)
    b58_address = models.CharField(blank=True, null=True, max_length=34, db_index=True)
    fiat_amount = models.DecimalField(blank=False, null=False, max_digits=10, decimal_places=2)
    satoshis = models.BigIntegerField(blank=True, null=True, db_index=True)
    currency_code_when_created = models.CharField(max_length=5, blank=False, null=False, db_index=True)
    confirmed_by_merchant_at = models.DateTimeField(blank=True, null=True, db_index=True)
    cancelled_at = models.DateTimeField(blank=True, null=True, db_index=True)
    funds_sent_at = models.DateTimeField(blank=True, null=True, db_index=True)
    expires_at = models.DateTimeField(blank=True, null=True, db_index=True)
    credential = models.ForeignKey('credentials.BaseCredential', blank=True, null=True)
    btc_transaction = models.ForeignKey(BTCTransaction, blank=True, null=True)
    merchant_email_sent_at = models.DateTimeField(blank=True, null=True, db_index=True)
    shopper_email_sent_at = models.DateTimeField(blank=True, null=True, db_index=True)
    objects = ShopperBTCPurchaseManager()

    def __str__(self):
        return '%s: %s' % (self.id, self.added_at)

    def save(self, *args, **kwargs):
        """
        Set fiat_amount when this object is first created
        http://stackoverflow.com/a/2311499/1754586
        """
        # Only do this for blockcypher and not BCI
        if not self.pk:
            # This only happens if the objects isn't in the database yet.
            self.currency_code_when_created = self.merchant.currency_code

            now_plus_15 = now() + datetime.timedelta(minutes=15)
            self.expires_at = now_plus_15
            self.satoshis = self.get_satoshis_from_fiat()
        super(ShopperBTCPurchase, self).save(*args, **kwargs)

    def get_satoshis_from_fiat(self):
        merchant = self.merchant
        currency_code = self.currency_code_when_created
        fiat_btc = BTCTransaction.get_btc_price(currency_code)
        basis_points_markup = merchant.basis_points_markup
        markup_fee = fiat_btc * basis_points_markup / 10000.00
        fiat_btc = fiat_btc + markup_fee
        total_btc = self.fiat_amount / Decimal(fiat_btc)
        satoshis = btc_to_satoshis(total_btc)
        return satoshis

    def format_mbtc_amount(self):
        return format_mbtc(satoshis_to_mbtc(self.satoshis))

    def pay_out_bitcoin(self, send_receipt=True):

        if not self.credential:
            self.credential = self.merchant.get_valid_api_credential()
            self.save()
        if self.b58_address:
            btc_txn = self.credential.send_btc(
                    satoshis_to_send=self.satoshis,
                    destination_btc_address=self.b58_address)
        else:
            btc_txn = self.credential.send_btc(
                    satoshis_to_send=self.satoshis,
                    destination_btc_address=None,
                    destination_email_address=self.shopper.email)
        self.btc_transaction = btc_txn
        self.confirmed_by_merchant_at = now()
        self.funds_sent_at = now()
        self.save()

        if send_receipt:
            self.send_shopper_receipt()
            self.send_merchant_receipt()

    def send_merchant_receipt(self):
        assert self.credential
        fiat_amount_formatted = self.get_fiat_amount_formatted()
        if self.btc_transaction:
            tx_hash = self.btc_transaction.txn_hash
        else:
            tx_hash = None
        body_context = {
                'fiat_amount_formatted': fiat_amount_formatted,
                'satoshis_formatted': self.format_satoshis_amount(),
                'shopper_email': self.shopper.email,
                'shopper_btc_address': self.b58_address,
                'business_name': self.merchant.business_name,
                'exchange_rate_formatted': self.get_exchange_rate_formatted(),
                'payment_method_formatted': self.credential.get_credential_to_display(),
                'payment_method': self.credential.get_credential_abbrev(),
                'tx_hash': tx_hash,
                }
        if self.shopper.name:
            body_context['salutataion'] = self.shopper.name
        email = send_and_log(
                subject='%s Received' % fiat_amount_formatted,
                body_template='merchant/shopper_cashin.html',
                to_merchant=self.merchant,
                body_context=body_context,
                )

        self.merchant_email_sent_at = now()
        self.save()

        return email

    def send_shopper_receipt(self):
        assert self.credential
        fiat_amount_formatted = self.get_fiat_amount_formatted()
        if self.btc_transaction:
            tx_hash = self.btc_transaction.txn_hash
        else:
            tx_hash = None
        body_context = {
                'fiat_amount_formatted': fiat_amount_formatted,
                'satoshis_formatted': self.format_satoshis_amount(),
                'shopper_name': self.shopper.name,
                'shopper_email': self.shopper.email,
                'shopper_btc_address': self.b58_address,
                'business_name': self.merchant.business_name,
                'exchange_rate_formatted': self.get_exchange_rate_formatted(),
                'payment_method_formatted': self.credential.get_credential_to_display(),
                'payment_method': self.credential.get_credential_abbrev(),
                'tx_hash': tx_hash,
                }
        email = send_and_log(
                subject='%s Received' % fiat_amount_formatted,
                body_template='shopper/cashin.html',
                to_merchant=None,
                to_name=self.shopper.name,
                to_email=self.shopper.email,
                body_context=body_context,
                )

        self.shopper_email_sent_at = now()
        self.save()

        return email
        pass

    def expires_at_unix_time(self):
        return int(self.expires_at.strftime('%s'))

    def get_shopper(self):
        return self.shopper

    def format_satoshis_amount(self):
        return format_satoshis_with_units(self.satoshis)

    def get_currency_symbol(self):
        if self.currency_code_when_created:
            return BFHCurrenciesList[self.currency_code_when_created]['symbol'].decode('utf-8')
        else:
            return '$'

    def get_fiat_amount_formatted(self):
        return '%s%s %s' % (self.get_currency_symbol(), self.fiat_amount,
                self.currency_code_when_created)

    def calculate_exchange_rate(self):
        return format_num_for_printing(float(self.fiat_amount) / satoshis_to_btc(self.satoshis), 2)

    def get_exchange_rate_formatted(self):
        return '%s%s %s' % (
                self.get_currency_symbol(),
                self.calculate_exchange_rate(),
                self.currency_code_when_created
                )

    def get_status(self):
        if self.cancelled_at:
            return _('Cancelled')
        if self.confirmed_by_merchant_at:
            return _('Complete')
        else:
            return _('Waiting on Merchant Approval')

    def get_type(self):
        return _('Sold BTC')
