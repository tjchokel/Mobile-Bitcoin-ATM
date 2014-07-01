# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BTSCredential'
        db.create_table(u'bitstamp_wallets_btscredential', (
            (u'basecredential_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['credentials.BaseCredential'], unique=True, primary_key=True)),
            ('customer_id', self.gf('django_fields.fields.EncryptedCharField')(max_length=101, block_type=None, cipher='AES', db_index=True)),
            ('api_key', self.gf('django_fields.fields.EncryptedCharField')(max_length=165, block_type=None, cipher='AES', db_index=True)),
            ('api_secret', self.gf('django_fields.fields.EncryptedCharField')(max_length=293, block_type=None, cipher='AES', db_index=True)),
        ))
        db.send_create_signal(u'bitstamp_wallets', ['BTSCredential'])

        # Adding model 'BTSSentBTC'
        db.create_table(u'bitstamp_wallets_btssentbtc', (
            (u'basesentbtc_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['credentials.BaseSentBTC'], unique=True, primary_key=True)),
            ('withdrawal_id', self.gf('django.db.models.fields.CharField')(max_length=64, db_index=True)),
            ('status', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=1, null=True, blank=True)),
            ('status_last_checked_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'bitstamp_wallets', ['BTSSentBTC'])


    def backwards(self, orm):
        # Deleting model 'BTSCredential'
        db.delete_table(u'bitstamp_wallets_btscredential')

        # Deleting model 'BTSSentBTC'
        db.delete_table(u'bitstamp_wallets_btssentbtc')


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
        u'bitstamp_wallets.btscredential': {
            'Meta': {'object_name': 'BTSCredential', '_ormbases': [u'credentials.BaseCredential']},
            'api_key': ('django_fields.fields.EncryptedCharField', [], {'max_length': '165', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'}),
            'api_secret': ('django_fields.fields.EncryptedCharField', [], {'max_length': '293', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'}),
            u'basecredential_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['credentials.BaseCredential']", 'unique': 'True', 'primary_key': 'True'}),
            'customer_id': ('django_fields.fields.EncryptedCharField', [], {'max_length': '101', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'})
        },
        u'bitstamp_wallets.btssentbtc': {
            'Meta': {'object_name': 'BTSSentBTC', '_ormbases': [u'credentials.BaseSentBTC']},
            u'basesentbtc_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['credentials.BaseSentBTC']", 'unique': 'True', 'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'status_last_checked_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'withdrawal_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'db_index': 'True'})
        },
        u'blockchain_wallets.bcicredential': {
            'Meta': {'object_name': 'BCICredential', '_ormbases': [u'credentials.BaseCredential']},
            u'basecredential_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['credentials.BaseCredential']", 'unique': 'True', 'primary_key': 'True'}),
            'main_password': ('django_fields.fields.EncryptedCharField', [], {'max_length': '293', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'}),
            'second_password': ('django_fields.fields.EncryptedCharField', [], {'block_type': 'None', 'max_length': '293', 'blank': 'True', 'null': 'True', 'cipher': "'AES'", 'db_index': 'True'}),
            'username': ('django_fields.fields.EncryptedCharField', [], {'max_length': '165', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'})
        },
        u'coinbase_wallets.cbscredential': {
            'Meta': {'object_name': 'CBSCredential', '_ormbases': [u'credentials.BaseCredential']},
            'api_key': ('django_fields.fields.EncryptedCharField', [], {'max_length': '293', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'}),
            'api_secret': ('django_fields.fields.EncryptedCharField', [], {'max_length': '549', 'block_type': 'None', 'cipher': "'AES'", 'db_index': 'True'}),
            u'basecredential_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['credentials.BaseCredential']", 'unique': 'True', 'primary_key': 'True'})
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
            'credential_link': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['credentials.CredentialLink']"}),
            'destination_btc_address': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '34', 'null': 'True', 'blank': 'True'}),
            'destination_email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polymorphic_ctype': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'polymorphic_credentials.basesentbtc_set'", 'null': 'True', 'to': u"orm['contenttypes.ContentType']"}),
            'satoshis': ('django.db.models.fields.BigIntegerField', [], {'db_index': 'True'}),
            'txn_hash': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '64', 'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'credentials.credentiallink': {
            'Meta': {'object_name': 'CredentialLink'},
            'bci_credential': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['blockchain_wallets.BCICredential']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'bts_credential': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['bitstamp_wallets.BTSCredential']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'cbs_credential': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['coinbase_wallets.CBSCredential']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum_confirmations': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'phone_num': ('phonenumber_field.modelfields.PhoneNumberField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.AuthUser']", 'null': 'True', 'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'})
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

    complete_apps = ['bitstamp_wallets']