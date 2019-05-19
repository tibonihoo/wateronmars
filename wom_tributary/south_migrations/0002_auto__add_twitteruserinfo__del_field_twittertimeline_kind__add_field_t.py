# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'TwitterUserInfo'
        db.create_table('wom_tributary_twitteruserinfo', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('oauth_access_token', self.gf('django.db.models.fields.TextField')()),
            ('oauth_access_token_secret', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('wom_tributary', ['TwitterUserInfo'])

        # Deleting field 'TwitterTimeline.kind'
        db.delete_column('wom_tributary_twittertimeline', 'kind')

        # Adding field 'TwitterTimeline.twitter_user_access_info'
        db.add_column('wom_tributary_twittertimeline', 'twitter_user_access_info',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['wom_tributary.TwitterUserInfo'], null=True),
                      keep_default=False)
        # Make sure no user info is actually null after the migration
        if not db.dry_run:
            for obj in orm.TwitterTimeline.objects.all():
                if obj.twitter_user_access_info is None:
                    info = orm.TwitterUserInfo(username=obj.username)
                    info.save()
                    obj.twitter_user_access_info = info
                    obj.save()


    def backwards(self, orm):
        # Deleting model 'TwitterUserInfo'
        db.delete_table('wom_tributary_twitteruserinfo')

        # Adding field 'TwitterTimeline.kind'
        db.add_column('wom_tributary_twittertimeline', 'kind',
                      self.gf('django.db.models.fields.CharField')(default='HOME', max_length=4),
                      keep_default=False)

        # Deleting field 'TwitterTimeline.twitter_user_access_info'
        db.delete_column('wom_tributary_twittertimeline', 'twitter_user_access_info_id')


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
            'twitter_user_access_info': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['wom_tributary.TwitterUserInfo']", 'null': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'wom_tributary.twitteruserinfo': {
            'Meta': {'object_name': 'TwitterUserInfo'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'oauth_access_token': ('django.db.models.fields.TextField', [], {}),
            'oauth_access_token_secret': ('django.db.models.fields.TextField', [], {}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['wom_tributary']
