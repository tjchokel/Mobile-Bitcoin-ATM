# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'BTCTransaction.met_confidence_threshold_at'
        db.add_column(u'bitcoins_btctransaction', 'met_confidence_threshold_at',
                      self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'BTCTransaction.blockcypher_preference'
        db.add_column(u'bitcoins_btctransaction', 'blockcypher_preference',
                      self.gf('django.db.models.fields.CharField')(db_index=True, max_length=6, null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'BTCTransaction.met_confidence_threshold_at'
        db.delete_column(u'bitcoins_btctransaction', 'met_confidence_threshold_at')

        # Deleting field 'BTCTransaction.blockcypher_preference'
        db.delete_column(u'bitcoins_btctransaction', 'blockcypher_preference')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'bitcoins.btctransaction': {
            'Meta': {'object_name': 'BTCTransaction'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'blockcypher_preference': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '6', 'null': 'True', 'blank': 'True'}),
            'conf_num': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'currency_code_when_created': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'destination_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.DestinationAddress']", 'null': 'True', 'blank': 'True'}),
            'fiat_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'forwarding_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.ForwardingAddress']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'irreversible_by': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'met_confidence_threshold_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'met_minimum_confirmation_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'min_confirmations_overrode_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'suspected_double_spend_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'txn_hash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'})
        },
        u'bitcoins.destinationaddress': {
            'Meta': {'object_name': 'DestinationAddress'},
            'b58_address': ('django.db.models.fields.CharField', [], {'max_length': '34', 'db_index': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['credentials.BaseCredential']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'retired_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        u'bitcoins.forwardingaddress': {
            'Meta': {'object_name': 'ForwardingAddress'},
            'b58_address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '34', 'db_index': 'True'}),
            'cancelled_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'customer_confirmed_deposit_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'destination_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.DestinationAddress']"}),
            'generated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_activity_check_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'paid_out_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'shopper': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoppers.Shopper']", 'null': 'True', 'blank': 'True'})
        },
        u'bitcoins.shopperbtcpurchase': {
            'Meta': {'object_name': 'ShopperBTCPurchase'},
            'added_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'b58_address': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '34', 'null': 'True', 'blank': 'True'}),
            'base_sent_btc': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['credentials.BaseSentBTC']", 'null': 'True', 'blank': 'True'}),
            'btc_transaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.BTCTransaction']", 'null': 'True', 'blank': 'True'}),
            'cancelled_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'confirmed_by_merchant_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['credentials.BaseCredential']", 'null': 'True', 'blank': 'True'}),
            'currency_code_when_created': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'fiat_amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'funds_sent_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'merchant_email_sent_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'shopper': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoppers.Shopper']"}),
            'shopper_email_sent_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'credentials.basecredential': {
            'Meta': {'object_name': 'BaseCredential'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'disabled_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_failed_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'last_succeded_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_credentials.basecredential_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"})
        },
        u'credentials.basesentbtc': {
            'Meta': {'object_name': 'BaseSentBTC'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['credentials.BaseCredential']"}),
            'destination_btc_address': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '34', 'null': 'True', 'blank': 'True'}),
            'destination_email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_credentials.basesentbtc_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'txn_hash': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'merchants.merchant': {
            'Meta': {'object_name': 'Merchant'},
            'address_1': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'address_2': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'basis_points_markup': ('django.db.models.fields.IntegerField', [], {'default': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'business_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'cashin_markup_in_bps': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'cashout_markup_in_bps': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'currency_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ignored_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'latitude_position': ('django.db.models.fields.DecimalField', [], {'db_index': 'True', 'null': 'True', 'max_digits': '18', 'decimal_places': '14', 'blank': 'True'}),
            'longitude_position': ('django.db.models.fields.DecimalField', [], {'db_index': 'True', 'null': 'True', 'max_digits': '18', 'decimal_places': '14', 'blank': 'True'}),
            'max_mbtc_shopper_purchase': ('django.db.models.fields.IntegerField', [], {'default': '1000', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'max_mbtc_shopper_sale': ('django.db.models.fields.IntegerField', [], {'default': '1000', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'minimum_confirmations': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'phone_num': ('phonenumber_field.modelfields.PhoneNumberField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.AuthUser']", 'null': 'True', 'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        u'shoppers.shopper': {
            'Meta': {'object_name': 'Shopper'},
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '34', 'null': 'True', 'blank': 'True'}),
            'phone_num': ('phonenumber_field.modelfields.PhoneNumberField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'})
        },
        u'users.authuser': {
            'Meta': {'object_name': 'AuthUser'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '60', 'null': 'True', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'phone_num': ('phonenumber_field.modelfields.PhoneNumberField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'phone_num_country': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['bitcoins']