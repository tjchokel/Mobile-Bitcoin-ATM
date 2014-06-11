from django.db import models
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from bitcoins.bci import set_bci_webhook
from bitcoins.blockcypher import set_blockcypher_webhook

from emails.trigger import send_and_log

from phones.models import SentSMS

from countries import BFHCurrenciesList

from bitcash.settings import BASE_URL, CAPITAL_CONTROL_COUNTRIES

from utils import (uri_to_url, simple_random_generator, satoshis_to_btc,
        satoshis_to_mbtc, format_mbtc, format_satoshis_with_units,
        format_num_for_printing)

import json
import requests
import math


class DestinationAddress(models.Model):
    """
    What's uploaded by the user.
    """
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)
    b58_address = models.CharField(blank=False, null=False, max_length=34, db_index=True)
    retired_at = models.DateTimeField(blank=True, null=True, db_index=True)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)

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
    destination_address = models.ForeignKey(DestinationAddress, blank=True, null=True)

    # technically, this is redundant through DestinationAddress
    # but having it here makes for easier querying (especially before there is a destination address)
    merchant = models.ForeignKey('merchants.Merchant', blank=False, null=False)
    shopper = models.ForeignKey('shoppers.Shopper', blank=True, null=True)
    user_confirmed_deposit_at = models.DateTimeField(blank=True, null=True, db_index=True)

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


class BTCTransaction(models.Model):
    """
    Deposits that affect our users.

    Both ForwardingAddress (initial send) and DestinationAddress (relay) are
    tracked separately in this same model.
    """
    added_at = models.DateTimeField(auto_now_add=True, db_index=True)
    txn_hash = models.CharField(max_length=64, blank=True, null=True,
            unique=True, db_index=True)
    satoshis = models.BigIntegerField(blank=True, null=True, db_index=True)
    conf_num = models.PositiveSmallIntegerField(blank=False, null=False, db_index=True)
    irreversible_by = models.DateTimeField(blank=True, null=True, db_index=True)
    suspected_double_spend_at = models.DateTimeField(blank=True, null=True, db_index=True)
    # We will always have this when they use a forwarding address (100% of the time until MPKs):
    forwarding_address = models.ForeignKey(ForwardingAddress, blank=True, null=True)
    # We will not have this on the initial deposit to the forwarding address:
    destination_address = models.ForeignKey(DestinationAddress, blank=True, null=True)
    # We will only have this on a forwarding transaction to the deposit transaction
    input_btc_transaction = models.ForeignKey('self', blank=True, null=True)
    fiat_amount = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    currency_code_when_created = models.CharField(max_length=5, blank=True, null=True, db_index=True)
    met_minimum_confirmation_at = models.DateTimeField(blank=True, null=True, db_index=True)

    def __str__(self):
        return '%s: %s' % (self.id, self.txn_hash)

    def get_merchant(self):
        return self.forwarding_address.merchant

    def get_shopper(self):
        return self.forwarding_address.shopper

    def save(self, *args, **kwargs):
        """
        Set fiat_amount when this object is first created
        http://stackoverflow.com/a/2311499/1754586
        """
        if not self.destination_address:
            # Only do this for blockcypher and not BCI
            if not self.pk:
                # This only happens if the objects isn't in the database yet.
                self.currency_code_when_created = self.get_merchant().currency_code
                self.fiat_amount = self.calculate_fiat_amount()

            if self.meets_minimum_confirmations() and not self.met_minimum_confirmation_at:
                # Mark it as such
                self.met_minimum_confirmation_at = now()

                # Send out emails
                self.send_merchant_txconfirmed_email()
                self.send_merchant_txconfirmed_sms()
                self.send_shopper_txconfirmed_email()
                self.send_shopper_txconfirmed_sms()
            elif not self.pk:
                # New (not in DB) and doesn't meet threshold
                self.send_shopper_newtx_email()
                self.send_shopper_newtx_sms()

        super(BTCTransaction, self).save(*args, **kwargs)

    def calculate_fiat_amount(self):
        merchant = self.get_merchant()
        currency_code = merchant.currency_code
        if currency_code in CAPITAL_CONTROL_COUNTRIES:
            url = 'https://conectabitcoin.com/en/market_prices.json'
            r = requests.get(url)
            content = json.loads(r.content)
            key = 'btc_'+currency_code.lower()
            fiat_btc = content[key]['sell']
        else:
            url = 'https://api.bitcoinaverage.com/ticker/global/'+currency_code
            r = requests.get(url)
            content = json.loads(r.content)
            fiat_btc = content['last']
        basis_points_markup = merchant.basis_points_markup
        markup_fee = fiat_btc * basis_points_markup / 10000.00
        fiat_btc = fiat_btc - markup_fee
        fiat_total = fiat_btc * satoshis_to_btc(self.satoshis)
        return math.floor(fiat_total*100)/100

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
            return 'Paid Out'
        if self.met_minimum_confirmation_at:
            return 'Sent'
        else:
            return 'Pending (%s of %s Confirms Needed)' % (
                    self.conf_num,
                    self.get_confs_needed(),
                    )

    def get_currency_symbol(self):
        if self.currency_code_when_created:
            return BFHCurrenciesList[self.currency_code_when_created]['symbol']
        else:
            return '$'

    def format_mbtc_amount(self):
        return format_mbtc(satoshis_to_mbtc(self.satoshis))

    def format_satoshis_amount(self):
        return format_satoshis_with_units(self.satoshis)

    def get_confs_needed(self):
        return self.get_merchant().minimum_confirmations

    def meets_minimum_confirmations(self):
        confirmations = self.conf_num
        confs_needed = self.get_confs_needed()
        return (confirmations and confirmations >= confs_needed)

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

    def send_shopper_newtx_email(self, force=False):
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
                    body_template='shopper_newtx.html',
                    to_merchant=None,
                    to_email=shopper.email,
                    to_name=shopper.name,
                    body_context=body_context,
                    )

    def send_shopper_newtx_sms(self):
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
            return SentSMS.send_and_log(
                    phone_num=shopper.phone_num,
                    message=msg,
                    to_user=None,
                    to_merchant=None,
                    to_shopper=shopper)

    def send_shopper_txconfirmed_email(self):
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
                    body_template='shopper_txconfirmed.html',
                    to_merchant=None,
                    to_email=shopper.email,
                    to_name=shopper.name,
                    body_context=body_context,
                    )

    def send_shopper_txconfirmed_sms(self):
        shopper = self.get_shopper()
        if shopper and shopper.phone_num:
            msg = 'The %s you sent to %s has been confirmed. They now owe you %s.'
            msg = msg % (
                    self.format_satoshis_amount(),
                    self.get_merchant().business_name,
                    self.get_fiat_amount_formatted(),
                    )
            return SentSMS.send_and_log(
                    phone_num=shopper.phone_num,
                    message=msg,
                    to_user=None,
                    to_merchant=None,
                    to_shopper=shopper)

    def send_merchant_txconfirmed_email(self):
        merchant = self.get_merchant()
        shopper = self.get_shopper()
        satoshis_formatted = self.format_satoshis_amount()
        body_context = {
                'satoshis_formatted': satoshis_formatted,
                'exchange_rate_formatted': self.get_exchange_rate_formatted(),
                'fiat_amount_formatted': self.get_fiat_amount_formatted(),
                'tx_hash': self.txn_hash,
                'closecoin_tx_uri': reverse('merchant_transactions'),
                }
        subject = '%s Received' % satoshis_formatted
        if shopper and shopper.name:
            subject += 'from %s' % shopper.name
            body_context['shopper_name'] = shopper.name
        return send_and_log(
                body_template='merchant_txconfirmed.html',
                subject='%s Received' % satoshis_formatted,
                to_merchant=merchant,
                body_context=body_context,
                )

    def send_merchant_txconfirmed_sms(self):
        if self.get_merchant().phone_num:
            # TODO: allow for notification settings
            msg = 'The %s you received from %s has been confirmed. Please pay them %s immediately.'
            shopper = self.get_shopper()
            if shopper and shopper.name:
                customer_string = shopper.name
            else:
                customer_string = 'the customer'
            msg = msg % (
                    self.format_satoshis_amount(),
                    customer_string,
                    self.merchant.business_name,
                    self.get_fiat_amount_formatted(),
                    )
            return SentSMS.send_and_log(
                    phone_num=self.merchant.phone_num,
                    message=msg,
                    to_user=self.merchant.user,
                    to_merchant=self.merchant,
                    to_shopper=shopper)
