# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'TwitterTimeline.twitter_user_access_info'
        db.alter_column('wom_tributary_twittertimeline', 'twitter_user_access_info_id', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['wom_tributary.TwitterUserInfo']))

    def backwards(self, orm):

        # Changing field 'TwitterTimeline.twitter_user_access_info'
        db.alter_column('wom_tributary_twittertimeline', 'twitter_user_access_info_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wom_tributary.TwitterUserInfo'], null=True))

    models = {
        'wom_pebbles.reference': {
            'Meta': {'object_name': 'Reference'},
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pin_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pub_date': ('django.db.models.fields.DateTimeField', [], {}),
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
            'twitter_user_access_info': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wom_tributary.TwitterUserInfo']"}),
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