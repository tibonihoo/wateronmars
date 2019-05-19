# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'WebFeed'
        db.create_table('wom_river_webfeed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wom_pebbles.Reference'])),
            ('xmlURL', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('last_update_check', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('wom_river', ['WebFeed'])


    def backwards(self, orm):
        # Deleting model 'WebFeed'
        db.delete_table('wom_river_webfeed')


    models = {
        'wom_pebbles.reference': {
            'Meta': {'object_name': 'Reference'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'save_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sources': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'productions'", 'symmetrical': 'False', 'to': "orm['wom_pebbles.Reference']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'wom_river.webfeed': {
            'Meta': {'object_name': 'WebFeed'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update_check': ('django.db.models.fields.DateTimeField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wom_pebbles.Reference']"}),
            'xmlURL': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['wom_river']