# -*- coding: utf-8 -*-

import feedparser
import datetime
from django.utils import timezone
from django.db import transaction

from celery.task.schedules import crontab  
from celery.decorators import periodic_task  
from celery import task

from wom_pebbles.models import Source
from wom_pebbles.models import Reference
from wom_river.models import FeedSource
from wom_river.utils.read_opml import parse_opml


@task()
def collect_new_pebbles_for_feed(feed):
  try:
    d = feedparser.parse(feed.xmlURL)
  except Exception,e:
    print "WARNING: skipping feed at %s because of a parse problem (%s))." % (feed.url,e)
    return
  is_public = feed.is_public
  # check feed info with d.feed.title
  feed_last_update = feed.last_update
  latest_item_date = feed_last_update
  for entry in d.entries:
    try:
      current_pebble_title = entry.title
      current_pebble_link = entry.link
    except Exception,e:
      print "WARNING: skipping item %s from feed at %s (%s)" % (entry.link,feed.url,e)
      continue
    candidates = Reference.objects.filter(url=current_pebble_link)
    if candidates:
      print "WARNING: found duplicate: %s" % candidates
      continue
    current_pebble_desc = entry.get("description","")
    if entry.has_key("updated_parsed"):
      updated_date_utc = entry.updated_parsed[:6]
    elif entry.has_key("published_parsed"):
      updated_date_utc = entry.published_parsed[:6]
    else:
      print "WARNING: using 'now' as date for item %s from feed at %s" % (entry.link,feed.url)
      updated_date_utc = timezone.now().utctimetuple()[:6]
    current_pebble_date = datetime.datetime(*(updated_date_utc),
                                             tzinfo=timezone.utc)
    if current_pebble_date < feed_last_update:
      continue
    r = Reference()
    r.title = current_pebble_title
    r.url   = current_pebble_link
    r.description = current_pebble_desc
    r.pub_date = current_pebble_date
    r.source = feed
    r.is_public = is_public
    r.save()
    for tag in feed.tags.all():
      r.tags.add(tag)
    r.save()
    if current_pebble_date > latest_item_date:
      latest_item_date = current_pebble_date
  feed.last_update = latest_item_date
  feed.save()
  

  
# this will run regularly, see http://celeryproject.org/docs/reference/celery.task.schedules.html#celery.task.schedules.crontab  
@periodic_task(run_every=crontab(hour="*", minute="*/20", day_of_week="*"))
def collect_all_new_pebbles():
  for feed in FeedSource.objects.iterator():
    collect_new_pebbles_for_feed.delay(feed)


@task()
def opml2db(opml_file,isPath=True,user_profile=None):
  collected_feeds,collected_tags = parse_opml(opml_file,isPath)
  from wom_classification.models import Tag
  from wom_river.models import FeedSource
  user_specific = user_profile is not None
  is_public = not user_specific
  db_new_tags = []
  user_tags = []
  for tag_as_text in collected_tags:
    known_candidates = Tag.objects.filter(name=tag_as_text)
    if not known_candidates:
      t = Tag()
      t.name = tag_as_text
      t.is_public = is_public
      db_new_tags.append(t)
    else:
      t = known_candidates[0]
  user_tags.append(t)
  db_new_feedsources = []
  user_feedsources = []
  for current_feed in collected_feeds:
    url_id = current_feed.htmlUrl or current_feed.xmlUrl
    known_candidates = FeedSource.objects.filter(url=url_id)
    if not known_candidates:
      f = FeedSource()
      f.name = current_feed.title
      f.xmlURL = current_feed.xmlUrl
      f.url = url_id
      f.last_update = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=timezone.utc)
      f.is_public = is_public
      f.save()
      for t in current_feed.tags:
        try:
          f.tags.add(Tag.objects.get(name=t))
        except:
          continue
      db_new_feedsources.append(f)
    else:
      f = known_candidates[0]
    user_feedsources.append(f)
  Tag.objects.bulk_create(db_new_tags)
  Source.objects.bulk_create(db_new_feedsources)
  with transaction.commit_on_succes():
    for f in db_new_feedsources:
      f.save()
  if user_specific:
    for t in user_tags:
      user_profile.tags.add(t)
    for f in user_feedsources:
      user_profile.sources.add(f)
      user_profile.feed_sources.add(f)
    user_profile.save()
