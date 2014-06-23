# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'OpenTime'
        db.create_table(u'merchants_opentime', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('merchant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['merchants.Merchant'])),
            ('weekday', self.gf('django.db.models.fields.IntegerField')(unique=True, db_index=True)),
            ('from_time', self.gf('django.db.models.fields.TimeField')()),
            ('to_time', self.gf('django.db.models.fields.TimeField')()),
        ))
        db.send_create_signal(u'merchants', ['OpenTime'])

        # Adding model 'MerchantWebsite'
        db.create_table(u'merchants_merchantwebsite', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('merchant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['merchants.Merchant'])),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200, db_index=True)),
            ('deleted_at', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'merchants', ['MerchantWebsite'])

        # Deleting field 'Merchant.hours'
        db.delete_column(u'merchants_merchant', 'hours')


    def backwards(self, orm):
        # Deleting model 'OpenTime'
        db.delete_table(u'merchants_opentime')

        # Deleting model 'MerchantWebsite'
        db.delete_table(u'merchants_merchantwebsite')

        # Adding field 'Merchant.hours'
        db.add_column(u'merchants_merchant', 'hours',
                      self.gf('django.db.models.fields.CharField')(blank=True, max_length=256, null=True, db_index=True),
                      keep_default=False)


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
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'minimum_confirmations': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'phone_num': ('phonenumber_field.modelfields.PhoneNumberField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.AuthUser']", 'null': 'True', 'blank': 'True'}),
            'zip_code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        u'merchants.merchantwebsite': {
            'Meta': {'object_name': 'MerchantWebsite'},
            'deleted_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'db_index': 'True'})
        },
        u'merchants.opentime': {
            'Meta': {'object_name': 'OpenTime'},
            'from_time': ('django.db.models.fields.TimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'merchant': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['merchants.Merchant']"}),
            'to_time': ('django.db.models.fields.TimeField', [], {}),
            'weekday': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'db_index': 'True'})
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

    complete_apps = ['merchants']