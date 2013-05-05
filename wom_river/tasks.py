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
from wom_river.models import ReferenceUserStatus
from wom_river.utils.read_opml import parse_opml

from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import URL_MAX_LENGTH
from wom_classification.models import TAG_NAME_MAX_LENGTH


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
  all_references = []
  for entry in d.entries:
    try:
      current_pebble_title = entry.title
      if len(current_pebble_title)>REFERENCE_TITLE_MAX_LENGTH:
        raise ValueError("Title '%s' too long." % current_pebble_title)
      current_pebble_link = entry.link
      if len(current_pebble_link)>URL_MAX_LENGTH:
        raise ValueError("URL '%s' too long." % current_pebble_link)
    except Exception,e:
      print "WARNING: skipping item %s from feed at %s (%s)" % (entry.link,feed.url,e)
      continue
    candidates = Reference.objects.filter(url=current_pebble_link)
    if candidates:
#      print "WARNING: found duplicate: %s" % candidates
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
    all_references.append(r)
    if current_pebble_date > latest_item_date:
      latest_item_date = current_pebble_date
  feed.last_update = latest_item_date
  with transaction.commit_on_success():
    for r in all_references:
      r.save()
  feed_tags = feed.tags.all()[:]
  with transaction.commit_on_success():
    for r in all_references:
      for tag in feed_tags:
        r.tags.add(tag)
      r.save()
    feed.save()


def collect_all_new_pebbles_sync():
  for feed in FeedSource.objects.iterator():
    collect_new_pebbles_for_feed(feed)

def delete_old_pebbles_sync():
  time_threshold = datetime.datetime.now(timezone.utc)-datetime.timedelta(weeks=12)
  Reference.objects.filter(save_count=0,pub_date__lt=time_threshold).delete()

# these will run regularly, see http://celeryproject.org/docs/reference/celery.task.schedules.html#celery.task.schedules.crontab  
@periodic_task(run_every=crontab(hour="*", minute="*/20", day_of_week="*"))
def collect_all_new_pebbles():
  collect_all_new_pebbles_sync()
  
@periodic_task(run_every=crontab(hour="*/12", day_of_week="*"))
def delete_old_pebbles():
  delete_old_pebbles_sync()


@task()  
def check_user_unread_feed_items(user):
  """
  Browse all feed sources registered by a given user and create as
  many UnreadReferenceByUser instances as there are unread items.
  """
  new_ref_status = []
  for source in user.userprofile.feed_sources.all():
    for ref in source.reference_set.all():
      if not ref.referenceuserstatus_set.filter(user=user).exists():
        rust = ReferenceUserStatus()
        rust.user = user
        rust.ref = ref
        rust.ref_pub_date = ref.pub_date
        new_ref_status.append(rust)
  with transaction.commit_on_success():
    for r in new_ref_status:
      r.save()

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
    # reject tags that are too long
    if len(tag_as_text) > TAG_NAME_MAX_LENGTH:
      continue
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
  feeds_and_tags = []
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
      feeds_and_tags.append((f,current_feed.tags))
      db_new_feedsources.append(f)
    else:
      f = known_candidates[0]
    user_feedsources.append(f)
  Tag.objects.bulk_create(db_new_tags)
  Source.objects.bulk_create(db_new_feedsources)
  with transaction.commit_on_success():
    for f in db_new_feedsources:
      f.save()
  for f,tags in feeds_and_tags:
    for t in tags:
      # reject tags that are too long
      if len(t) > TAG_NAME_MAX_LENGTH:
        continue
      try:
        f.tags.add(Tag.objects.get(name=t))
      except:
        continue
    f.save()
  if user_specific:
    for t in user_tags:
      user_profile.tags.add(t)
    for f in user_feedsources:
      user_profile.sources.add(f)
      user_profile.feed_sources.add(f)
    user_profile.save()
