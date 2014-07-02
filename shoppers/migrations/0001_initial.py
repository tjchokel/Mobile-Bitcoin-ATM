# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Shopper'
        db.create_table(u'shoppers_shopper', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=34, null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(db_index=True, max_length=75, null=True, blank=True)),
            ('phone_num', self.gf('phonenumber_field.modelfields.PhoneNumberField')(db_index=True, max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal(u'shoppers', ['Shopper'])


    def backwards(self, orm):
        # Deleting model 'Shopper'
        db.delete_table(u'shoppers_shopper')


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