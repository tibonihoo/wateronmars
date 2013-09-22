# -*- coding: utf-8 -*-

import feedparser
import datetime
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from celery.task.schedules import crontab  
from celery.decorators import periodic_task  
from celery import task

from wom_pebbles.models import Source
from wom_pebbles.models import Reference
from wom_river.models import FeedSource
from wom_river.models import ReferenceUserStatus
from wom_river.utils.read_opml import parse_opml
from wom_river.utils.netscape_bookmarks import parse_netscape_bookmarks

from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import URL_MAX_LENGTH
from wom_classification.models import TAG_NAME_MAX_LENGTH

from wom_user.forms import UserBookmarkAdditionForm

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
      feeds_and_tags.append((f,current_feed.tags))
    user_feedsources.append(f)
  with transaction.commit_on_success():
    for f in db_new_feedsources:
      f.save()
    for t in db_new_tags:
      t.save()
  with transaction.commit_on_success():
    for f,tags in feeds_and_tags:
      for t in tags:
        # reject tags that are too long
        if len(t) > TAG_NAME_MAX_LENGTH:
          continue
        try:
          f.tags.add(Tag.objects.get(name=t))
        except Exception,e:
          print e
          continue
      f.save()
  if user_specific:
    for t in user_tags:
      user_profile.tags.add(t)
    for f in user_feedsources:
      user_profile.sources.add(f)
      user_profile.feed_sources.add(f)
    user_profile.save()

@task()
def nsbmk2db(nsbmk_file,user):
  from wom_classification.models import Tag
  collected_bmks = parse_netscape_bookmarks(nsbmk_file)
  bookmarks_to_save  = []
  for bmk_info in collected_bmks:
    bmk_dict = {
      "url": bmk_info["url"],
      }
    if "title" in bmk_info:
      bmk_dict["title"] = bmk_info["title"]
    if "note" in bmk_info:
      bmk_dict["description"] = bmk_info["note"]
    addition_form = UserBookmarkAdditionForm(user,bmk_dict)
    print "trying to import bmk %s" % bmk_dict
    if addition_form.is_valid():
      b = addition_form.save()
      for tag_name in bmk_info.get("tags","").split(","):
        tag_name = tag_name[:TAG_NAME_MAX_LENGTH]
        try:
          t = Tag.objects.get(name=tag_name)
        except ObjectDoesNotExist:
          t = Tag()
          t.name = tag_name
          t.is_public = True
          t.save()
        b.tags.add(t)
      bookmarks_to_save.append(b)
      if bmk_info.get("private","1")=="0":
        b.is_public = True
      if "posix_timestamp" in bmk_info:
        b.pub_date = datetime.datetime.utcfromtimestamp(float(bmk_info["posix_timestamp"]))
    else:
      print "form invalid"
      print addition_form.non_field_errors()
      print addition_form.errors
  with transaction.commit_on_success():
    for b in bookmarks_to_save:
      b.save()
      print "Saved %s" % b
      
