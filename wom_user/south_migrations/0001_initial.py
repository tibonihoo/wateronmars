# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserProfile'
        db.create_table('wom_user_userprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
        ))
        db.send_create_signal('wom_user', ['UserProfile'])

        # Adding M2M table for field web_feeds on 'UserProfile'
        db.create_table('wom_user_userprofile_web_feeds', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['wom_user.userprofile'], null=False)),
            ('webfeed', models.ForeignKey(orm['wom_river.webfeed'], null=False))
        ))
        db.create_unique('wom_user_userprofile_web_feeds', ['userprofile_id', 'webfeed_id'])

        # Adding M2M table for field sources on 'UserProfile'
        db.create_table('wom_user_userprofile_sources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['wom_user.userprofile'], null=False)),
            ('reference', models.ForeignKey(orm['wom_pebbles.reference'], null=False))
        ))
        db.create_unique('wom_user_userprofile_sources', ['userprofile_id', 'reference_id'])

        # Adding M2M table for field public_sources on 'UserProfile'
        db.create_table('wom_user_userprofile_public_sources', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('userprofile', models.ForeignKey(orm['wom_user.userprofile'], null=False)),
            ('reference', models.ForeignKey(orm['wom_pebbles.reference'], null=False))
        ))
        db.create_unique('wom_user_userprofile_public_sources', ['userprofile_id', 'reference_id'])

        # Adding model 'UserBookmark'
        db.create_table('wom_user_userbookmark', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wom_pebbles.Reference'])),
            ('saved_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('is_public', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('comment', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal('wom_user', ['UserBookmark'])

        # Adding model 'ReferenceUserStatus'
        db.create_table('wom_user_referenceuserstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('reference', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wom_pebbles.Reference'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('reference_pub_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('has_been_read', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('has_been_saved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('main_source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', to=orm['wom_pebbles.Reference'])),
        ))
        db.send_create_signal('wom_user', ['ReferenceUserStatus'])


    def backwards(self, orm):
        # Deleting model 'UserProfile'
        db.delete_table('wom_user_userprofile')

        # Removing M2M table for field web_feeds on 'UserProfile'
        db.delete_table('wom_user_userprofile_web_feeds')

        # Removing M2M table for field sources on 'UserProfile'
        db.delete_table('wom_user_userprofile_sources')

        # Removing M2M table for field public_sources on 'UserProfile'
        db.delete_table('wom_user_userprofile_public_sources')

        # Deleting model 'UserBookmark'
        db.delete_table('wom_user_userbookmark')

        # Deleting model 'ReferenceUserStatus'
        db.delete_table('wom_user_referenceuserstatus')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
        },
        'wom_user.referenceuserstatus': {
            'Meta': {'object_name': 'ReferenceUserStatus'},
            'has_been_read': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_been_saved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'main_source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['wom_pebbles.Reference']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wom_pebbles.Reference']"}),
            'reference_pub_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'wom_user.userbookmark': {
            'Meta': {'object_name': 'UserBookmark'},
            'comment': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'reference': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wom_pebbles.Reference']"}),
            'saved_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        'wom_user.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'owner': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'public_sources': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'publicly_related_userprofile'", 'symmetrical': 'False', 'to': "orm['wom_pebbles.Reference']"}),
            'sources': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'userprofile'", 'symmetrical': 'False', 'to': "orm['wom_pebbles.Reference']"}),
            'web_feeds': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wom_river.WebFeed']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['wom_user']