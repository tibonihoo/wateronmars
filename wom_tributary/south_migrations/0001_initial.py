# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'GeneratedFeed'
        db.create_table('wom_tributary_generatedfeed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('provider', self.gf('django.db.models.fields.CharField')(default='TWTR', max_length=4)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wom_pebbles.Reference'])),
            ('last_update_check', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('wom_tributary', ['GeneratedFeed'])

        # Adding model 'TwitterTimeline'
        db.create_table('wom_tributary_twittertimeline', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('generated_feed', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['wom_tributary.GeneratedFeed'], unique=True)),
            ('kind', self.gf('django.db.models.fields.CharField')(default='HOME', max_length=4)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('wom_tributary', ['TwitterTimeline'])


    def backwards(self, orm):
        # Deleting model 'GeneratedFeed'
        db.delete_table('wom_tributary_generatedfeed')

        # Deleting model 'TwitterTimeline'
        db.delete_table('wom_tributary_twittertimeline')


    models = {
        'wom_pebbles.reference': {
            'Meta': {'object_name': 'Reference'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'save_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'sources': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'productions'", 'symmetrical': 'False', 'to': "orm['wom_pebbles.Reference']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'wom_tributary.generatedfeed': {
            'Meta': {'object_name': 'GeneratedFeed'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update_check': ('django.db.models.fields.DateTimeField', [], {}),
            'provider': ('django.db.models.fields.CharField', [], {'default': "'TWTR'", 'max_length': '4'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wom_pebbles.Reference']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'wom_tributary.twittertimeline': {
            'Meta': {'object_name': 'TwitterTimeline'},
            'generated_feed': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['wom_tributary.GeneratedFeed']", 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.CharField', [], {'default': "'HOME'", 'max_length': '4'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['wom_tributary']