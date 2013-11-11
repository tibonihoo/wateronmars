# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

from celery import task

import feedparser
import datetime
from django.utils import timezone
from django.db import transaction

from wom_pebbles.models import Reference
from wom_river.models import FeedSource
from wom_river.models import ReferenceUserStatus
from wom_river.utils.read_opml import parse_opml

from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import URL_MAX_LENGTH


@task()
def collect_new_references_for_feed(feed):
  """Get the feed data from its URL and collect the new references into the db."""
  try:
    d = feedparser.parse(feed.xmlURL)
  except Exception,e:
    print "WARNING: skipping feed at %s because of a parse problem (%s))."\
      % (feed.url,e)
    return
  is_public = feed.is_public
  # check feed info with d.feed.title
  feed_last_update_check = feed.last_update_check
  latest_item_date = feed_last_update_check
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
    if current_pebble_date < feed_last_update_check:
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
  feed.last_update_check = latest_item_date
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


def collect_all_new_references_sync():
  for feed in FeedSource.objects.iterator():
    collect_new_references_for_feed(feed)

def delete_old_references_sync():
  time_threshold = datetime.datetime.now(timezone.utc)-datetime.timedelta(weeks=12)
  Reference.objects.filter(save_count=0,pub_date__lt=time_threshold).delete()


class FakeReferenceUserStatus:

  def __init__(self):
    self.user = None 
    
def generate_reference_user_status(user,references):
  """Generate reference user status instances for a given list of references.
  WARNING: the new instances are not saved in the database!
  If user is None, then the created instances are not saveable at all.
  """
  new_ref_status = []
  for ref in references.select_related("referenceuserstatus_set").all():
    if user and not ref.referenceuserstatus_set.filter(user=user).exists():
      rust = ReferenceUserStatus()
      rust.user = user
      rust.ref = ref
      rust.ref_pub_date = ref.pub_date
      new_ref_status.append(rust)
      # TODO: check here that the corresponding reference has not
      # been saved already !
    elif user is None:
      rust = FakeReferenceUserStatus()
      rust.ref = ref
      rust.ref_pub_date = ref.pub_date
      new_ref_status.append(rust)      
  return new_ref_status

@task()  
def check_user_unread_feed_items(user):
  """
  Browse all feed sources registered by a given user and create as
  many UnreadReferenceByUser instances as there are unread items.
  """
  new_ref_status = []
  for source in user.userprofile.feed_sources.select_related("reference_set").all():
    new_ref_status += generate_reference_user_status(user,source.reference_set.select_related("referenceuserstatus_set").all())
  with transaction.commit_on_success():
    for r in new_ref_status:
      r.save()


@task()
def import_feedsources_from_opml(opml_txt):
  """
  Save in the db the FeedSources found in the OPML-formated text.
  opml_txt: a unicode string representing the content of a full OPML file.
  Return a dictionary assiociating each feed with a set of tags {feed:tagSet,...).
  """
  collected_feeds,collected_tags = parse_opml(opml_txt,False)
  db_new_feedsources = []
  feeds_and_tags = []
  for current_feed in collected_feeds:
    url_id = current_feed.htmlUrl or current_feed.xmlUrl
    known_candidates = FeedSource.objects.filter(url=url_id)
    if not known_candidates:
      f = FeedSource()
      f.name = current_feed.title
      f.xmlURL = current_feed.xmlUrl
      f.url = url_id
      f.last_update_check = datetime.datetime.utcfromtimestamp(0)\
                                             .replace(tzinfo=timezone.utc)
      feeds_and_tags.append((f,current_feed.tags))
      db_new_feedsources.append(f)
    else:
      f = known_candidates[0]
      feeds_and_tags.append((f,current_feed.tags))
  with transaction.commit_on_success():
    for f in db_new_feedsources:
      f.save()
  return dict(feeds_and_tags)
  
# TODO put this in a function of wom_user with the appropriate tests.
  # with transaction.commit_on_success():
  #   for f,tags in feeds_and_tags:
  #     source_tag_setter(user,f,tags)
  #     f.save()
  #   userprofile.feed_source.add(f)
  #   userprofile.source.add(f)

