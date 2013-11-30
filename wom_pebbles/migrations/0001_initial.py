# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Reference'
        db.create_table('wom_pebbles_reference', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('description', self.gf('django.db.models.fields.TextField')(default='')),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('save_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('wom_pebbles', ['Reference'])

        # Adding M2M table for field sources on 'Reference'
        db.create_table('wom_pebbles_reference_sources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_reference', models.ForeignKey(orm['wom_pebbles.reference'], null=False)),
            ('to_reference', models.ForeignKey(orm['wom_pebbles.reference'], null=False))
        ))
        db.create_unique('wom_pebbles_reference_sources', ['from_reference_id', 'to_reference_id'])


    def backwards(self, orm):
        # Deleting model 'Reference'
        db.delete_table('wom_pebbles_reference')

        # Removing M2M table for field sources on 'Reference'
        db.delete_table('wom_pebbles_reference_sources')


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
        }
    }

    complete_apps = ['wom_pebbles']