# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Source'
        db.create_table('wom_pebbles_source', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(unique=True, max_length=512)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('description', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal('wom_pebbles', ['Source'])

        # Adding M2M table for field tags on 'Source'
        db.create_table('wom_pebbles_source_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('source', models.ForeignKey(orm['wom_pebbles.source'], null=False)),
            ('tag', models.ForeignKey(orm['wom_classification.tag'], null=False))
        ))
        db.create_unique('wom_pebbles_source_tags', ['source_id', 'tag_id'])

        # Adding model 'Reference'
        db.create_table('wom_pebbles_reference', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=512)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('description', self.gf('django.db.models.fields.TextField')(default='')),
            ('pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wom_pebbles.Source'])),
        ))
        db.send_create_signal('wom_pebbles', ['Reference'])

        # Adding M2M table for field tags on 'Reference'
        db.create_table('wom_pebbles_reference_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('reference', models.ForeignKey(orm['wom_pebbles.reference'], null=False)),
            ('tag', models.ForeignKey(orm['wom_classification.tag'], null=False))
        ))
        db.create_unique('wom_pebbles_reference_tags', ['reference_id', 'tag_id'])


    def backwards(self, orm):
        # Deleting model 'Source'
        db.delete_table('wom_pebbles_source')

        # Removing M2M table for field tags on 'Source'
        db.delete_table('wom_pebbles_source_tags')

        # Deleting model 'Reference'
        db.delete_table('wom_pebbles_reference')

        # Removing M2M table for field tags on 'Reference'
        db.delete_table('wom_pebbles_reference_tags')


    models = {
        'wom_classification.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'wom_pebbles.reference': {
            'Meta': {'object_name': 'Reference'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wom_pebbles.Source']"}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wom_classification.Tag']", 'symmetrical': 'False'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '512'})
        },
        'wom_pebbles.source': {
            'Meta': {'object_name': 'Source'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wom_classification.Tag']", 'symmetrical': 'False'}),
            'url': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '512'})
        }
    }

    complete_apps = ['wom_pebbles']