# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'FeedSource'
        db.create_table('wom_river_feedsource', (
            ('source_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['wom_pebbles.Source'], unique=True, primary_key=True)),
            ('xmlURL', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('wom_river', ['FeedSource'])


    def backwards(self, orm):
        # Deleting model 'FeedSource'
        db.delete_table('wom_river_feedsource')


    models = {
        'wom_classification.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'wom_pebbles.source': {
            'Meta': {'object_name': 'Source'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wom_classification.Tag']", 'symmetrical': 'False'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'})
        },
        'wom_river.feedsource': {
            'Meta': {'object_name': 'FeedSource', '_ormbases': ['wom_pebbles.Source']},
            'last_update': ('django.db.models.fields.DateTimeField', [], {}),
            'source_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['wom_pebbles.Source']", 'unique': 'True', 'primary_key': 'True'}),
            'xmlURL': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        }
    }

    complete_apps = ['wom_river']