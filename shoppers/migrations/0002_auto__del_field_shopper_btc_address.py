# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Shopper.btc_address'
        db.delete_column(u'shoppers_shopper', 'btc_address_id')


    def backwards(self, orm):
        # Adding field 'Shopper.btc_address'
        db.add_column(u'shoppers_shopper', 'btc_address',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['bitcoins.ForwardingAddress'], null=True, blank=True),
                      keep_default=False)


    models = {
        u'shoppers.shopper': {
            'Meta': {'object_name': 'Shopper'},
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '34', 'null': 'True', 'blank': 'True'}),
            'phone_num': ('phonenumber_field.modelfields.PhoneNumberField', [], {'db_index': 'True', 'max_length': '128', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['shoppers']