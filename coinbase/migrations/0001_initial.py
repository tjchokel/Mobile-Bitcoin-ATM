# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CBCredential'
        db.create_table(u'coinbase_cbcredential', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('merchant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['merchants.Merchant'])),
            ('api_key', self.gf('django_fields.fields.EncryptedCharField')(block_type=None, max_length=165, blank=True, null=True, cipher='AES', db_index=True)),
            ('api_secret', self.gf('django_fields.fields.EncryptedCharField')(block_type=None, max_length=293, blank=True, null=True, cipher='AES', db_index=True)),
            ('disabled_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
            ('last_verified_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'coinbase', ['CBCredential'])

        # Adding model 'SellOrder'
        db.create_table(u'coinbase_sellorder', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('cb_credential', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coinbase.CBCredential'])),
            ('btc_transaction', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bitcoins.BTCTransaction'], null=True, blank=True)),
            ('cb_code', self.gf('django.db.models.fields.CharField')(max_length=32, db_index=True)),
            ('received_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('satoshis', self.gf('django.db.models.fields.BigIntegerField')(db_index=True)),
            ('currency_code', self.gf('django.db.models.fields.CharField')(max_length=5, db_index=True)),
            ('fees_in_fiat', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2, db_index=True)),
            ('to_receive_in_fiat', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=2, db_index=True)),
        ))
        db.send_create_signal(u'coinbase', ['SellOrder'])

        # Adding model 'CurrentBalance'
        db.create_table(u'coinbase_currentbalance', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('cb_credential', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coinbase.CBCredential'])),
            ('satoshis', self.gf('django.db.models.fields.BigIntegerField')(db_index=True)),
        ))
        db.send_create_signal(u'coinbase', ['CurrentBalance'])

        # Adding model 'SendBTC'
        db.create_table(u'coinbase_sendbtc', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('cb_credential', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['coinbase.CBCredential'])),
            ('received_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True)),
            ('txn_hash', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=64, unique=True, null=True, blank=True)),
            ('satoshis', self.gf('django.db.models.fields.BigIntegerField')(db_index=True)),
            ('destination_address', self.gf('django.db.models.fields.CharField')(max_length=34, db_index=True)),
            ('cb_id', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('notes', self.gf('django.db.models.fields.CharField')(max_length=2048)),
        ))
        db.send_create_signal(u'coinbase', ['SendBTC'])


    def backwards(self, orm):
        # Deleting model 'CBCredential'
        db.delete_table(u'coinbase_cbcredential')

        # Deleting model 'SellOrder'
        db.delete_table(u'coinbase_sellorder')

        # Deleting model 'CurrentBalance'
        db.delete_table(u'coinbase_currentbalance')

        # Deleting model 'SendBTC'
        db.delete_table(u'coinbase_sendbtc')


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
            'conf_num': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'}),
            'currency_code_when_created': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '5', 'null': 'True', 'blank': 'True'}),
            'destination_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.DestinationAddress']", 'null': 'True', 'blank': 'True'}),
            'fiat_amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '2', 'blank': 'True'}),
            'forwarding_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.ForwardingAddress']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_btc_transaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.BTCTransaction']", 'null': 'True', 'blank': 'True'}),
            'irreversible_by': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'met_minimum_confirmation_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'suspected_double_spend_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'txn_hash': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'bitcoins.destinationaddress': {
            'Meta': {'object_name': 'DestinationAddress'},
            'b58_address': ('django.db.models.fields.CharField', [], {'max_length': '34', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'retired_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'uploaded_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'})
        },
        u'bitcoins.forwardingaddress': {
            'Meta': {'object_name': 'ForwardingAddress'},
            'b58_address': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '34', 'db_index': 'True'}),
            'customer_confirmed_deposit_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'destination_address': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.DestinationAddress']", 'null': 'True', 'blank': 'True'}),
            'generated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'paid_out_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'shopper': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['shoppers.Shopper']", 'null': 'True', 'blank': 'True'})
        },
        u'coinbase.cbcredential': {
            'Meta': {'object_name': 'CBCredential'},
            'api_key': ('django_fields.fields.EncryptedCharField', [], {'block_type': 'None', 'max_length': '165', 'blank': 'True', 'null': 'True', 'cipher': "'AES'", 'db_index': 'True'}),
            'api_secret': ('django_fields.fields.EncryptedCharField', [], {'block_type': 'None', 'max_length': '293', 'blank': 'True', 'null': 'True', 'cipher': "'AES'", 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'disabled_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_verified_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"})
        },
        u'coinbase.currentbalance': {
            'Meta': {'object_name': 'CurrentBalance'},
            'cb_credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coinbase.CBCredential']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'})
        },
        u'coinbase.sellorder': {
            'Meta': {'object_name': 'SellOrder'},
            'btc_transaction': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['bitcoins.BTCTransaction']", 'null': 'True', 'blank': 'True'}),
            'cb_code': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'cb_credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coinbase.CBCredential']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'currency_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'fees_in_fiat': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'received_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'to_receive_in_fiat': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2', 'db_index': 'True'})
        },
        u'coinbase.sendbtc': {
            'Meta': {'object_name': 'SendBTC'},
            'cb_credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['coinbase.CBCredential']"}),
            'cb_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'destination_address': ('django.db.models.fields.CharField', [], {'max_length': '34', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'received_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'txn_hash': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'merchants.merchant': {
            'Meta': {'object_name': 'Merchant'},
            'address_1': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'address_2': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'basis_points_markup': ('django.db.models.fields.IntegerField', [], {'default': '100', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'business_name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'country': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'currency_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'hours': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['coinbase']