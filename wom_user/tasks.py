# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2013-2019 Thibauld Nion
#
# This file is part of WaterOnMars (https://github.com/tibonihoo/wateronmars) 
#
# WaterOnMars is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# WaterOnMars is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with WaterOnMars.  If not, see <http://www.gnu.org/licenses/>.
#

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned

from datetime import datetime
from django.utils import timezone

from django.conf import settings
from wom_user.settings import (
    WEB_FEED_COLLATION_MIN_NUM_REF_TARGET,
    WEB_FEED_COLLATION_MAX_NUM_REF_TARGET,
    WEB_FEED_COLLATION_TIMEOUT
    )

if settings.USE_CELERY:
  from celery.task.schedules import crontab  
  from celery.decorators import periodic_task  
  from celery.decorators import task  
else:
  def crontab(*args,**kwargs):
    return None
  def periodic_task(*args,**kwargs):
    def wrap(f):
      return f
    return wrap
  def task(*args,**kwargs):
    def wrap(f):
      return f
    return wrap


    
from wom_pebbles.tasks import delete_old_unpinned_references
from wom_pebbles.tasks import import_references_from_ns_bookmark_list

from wom_river.tasks import (
    collect_news_from_feeds,
    import_feedsources_from_opml,
    generate_collations
    )

from wom_pebbles.models import Reference
from wom_user.models import UserBookmark
from wom_user.models import UserProfile
from wom_user.models import ReferenceUserStatus

from wom_classification.models import TAG_NAME_MAX_LENGTH
from wom_classification.models import set_item_tag_names

from wom_river.models import WebFeed

from wom_tributary.tasks import (
    collect_news_from_tweeter_feeds,
    collect_news_from_mastodon_feeds
    )
from wom_tributary.models import GeneratedFeed

import logging
logger = logging.getLogger(__name__)

# Tasks to be run regularly.
# http://celeryproject.org/docs/reference/celery.task.schedules.html#celery.task.schedules.crontab


@periodic_task(run_every=crontab(hour="*", minute="*/20", day_of_week="*"))
def collect_all_new_references_regularly():
  collect_news_from_followed_feeds()

@periodic_task(run_every=crontab(hour="*/1", day_of_week="*"))
def collect_all_new_twitter_references_regularly():
  collect_news_from_tweeter_feeds(1)

@periodic_task(run_every=crontab(hour="*/1", day_of_week="*"))
def collect_all_new_mastodon_references_regularly():
  collect_news_from_mastodon_feeds(1)

@periodic_task(run_every=crontab(hour="*/12", day_of_week="*"))
def delete_obsolete_unpinned_references_regularly():
  delete_obsolete_unpinned_references_from_feeds()


def collect_news_from_followed_feeds():
  feeds = WebFeed.objects.exclude(userprofile=None).iterator()
  collect_news_from_feeds(feeds)


@task()
def import_user_bookmarks_from_ns_list(user,nsbmk_txt):
  ref_and_metadata = import_references_from_ns_bookmark_list(nsbmk_txt)
  bmk_to_process = []
  for ref,meta in ref_and_metadata.items():
    try:
      bmk = UserBookmark.objects.get(owner=user,reference=ref)
    except ObjectDoesNotExist:
      bmk = UserBookmark(owner=user,reference=ref,
                         saved_date=ref.pub_date)
      ref.add_pin()
      for src in ref.sources.all():
        user.userprofile.sources.add(src)
    bmk.is_public = meta.is_public
    bmk.comment = meta.note
    # pile up the bookmarks for tag attribution
    bmk_to_process.append((bmk,meta))
  with transaction.atomic():
    for b,_ in bmk_to_process:
      b.reference.save()
      b.save()
  classif_data_to_save = []
  for bmk,meta in bmk_to_process:
    valid_tags = [t for t in meta.tags if len(t)<=TAG_NAME_MAX_LENGTH]
    if len(valid_tags)!=len(meta.tags):
      invalid_tags = [t for t in meta.tags if len(t)>TAG_NAME_MAX_LENGTH]
      logger.error("Could not import some bmk tags with too long names (%s>%s)"\
                   % (",".join(len(t) for t in invalid_tags),TAG_NAME_MAX_LENGTH))
    classif_data_to_save.append(set_item_tag_names(user,bmk.reference,valid_tags))
  with transaction.atomic():
    for cd in classif_data_to_save:
      cd.save()


@task()
def import_user_feedsources_from_opml(user,opml_txt):
  feeds_and_tags = import_feedsources_from_opml(opml_txt)
  profile = UserProfile.objects.get(owner=user)
  classif_data_to_save = []
  for feed,tags in feeds_and_tags.items():
    profile.web_feeds.add(feed)
    profile.sources.add(feed.source)
    valid_tags = [t for t in tags if len(t)<=TAG_NAME_MAX_LENGTH]
    if len(valid_tags)!=len(tags):
      invalid_tags = [t for t in tags if len(t)>TAG_NAME_MAX_LENGTH]
      logger.error("Could not import some source tags with too long names (%s>%s)"\
                   % (",".join(str(len(t)) for t in invalid_tags),
                      TAG_NAME_MAX_LENGTH))
    classif_data_to_save.append(set_item_tag_names(user,feed,valid_tags))
  with transaction.atomic():
    for cd in classif_data_to_save:
      cd.save()


class FakeReferenceUserStatus:

  def __init__(self):
    self.user = None 


def get_unknown_reference():
  """Returns 'the' Reference representing an unknown source.
  NOTE: Will create it if it hasn't been created yet.
  """
  try:
    return Reference.objects.get(url="<unknown>")
  except ObjectDoesNotExist:
    s = Reference(url="<unknown>",title="<unknown>",
                  pin_count=1,
                  pub_date=datetime.utcfromtimestamp(0)\
                  .replace(tzinfo=timezone.utc))        
    s.save()
    return s

  
def generate_reference_user_status(user,references):
  """Generate reference user status instances for a given set of references.
  WARNING: the new instances are not saved in the database!
  """
  new_ref_status = []
  for ref in references:
    source_query = ref.sources.filter(userprofile=user.userprofile)\
                              .distinct().order_by("pub_date")
    try:
      s = source_query.get()
    except MultipleObjectsReturned:
      s = source_query.all()[0]
    except ObjectDoesNotExist:
      s = get_unknown_reference()
    rust = ReferenceUserStatus()
    rust.main_source = s
    rust.owner = user
    rust.reference = ref
    rust.reference_pub_date = ref.pub_date
    new_ref_status.append(rust)
  return new_ref_status


def clean_corrupted_rusts(user):
  """Check that a user's ReferenceUserStatus still correspond to a
  valid reference and a valid main_source.
  """
  # first cleanup strange corruption happening sometimes in the db
  for rust in ReferenceUserStatus.objects.filter(owner=user,has_been_read=False):
    corrupted = False
    try:
      rust_ref = str(rust.reference)
    except ObjectDoesNotExist:
      rust_ref = "not-found"
      corrupted = True
    except Exception as e:
      rust_ref = "err(%s)" % e
    try:
      rust_src = str(rust.main_source)
    except ObjectDoesNotExist:
      rust_src = "not-found"
      corrupted = True
    except Exception as e:
      rust_src = "err(%s)" % e
    if corrupted:
      logger.warning("Deleting corrupted ReferenceUserStatus: \
read %s, pub_date %s, reference %s, source %s." \
                     % (rust.has_been_read,rust.reference_pub_date,
                        rust_ref,rust_src))
      try:
        rust.delete()
      except Exception as e:
        logger.error("Could not delete a corrupted ReferenceUserStatus (%s)." % e)
        continue

# TODO test
def build_feed_collation_map(user):
  collating_feeds = user.userprofile.collating_feeds.select_related("feed").all()
  return {cf.feed: cf for cf in collating_feeds}

    
@task()  
def check_user_unread_feed_items(user):
  """Browse all feed sources registered by a given user and create as
  many ReferenceUserStatus instances as there are unread items.

  NOTE: will avoid creating 2 reference user statuses pointing to a
  same reference.
  """
  clean_corrupted_rusts(user)
  new_ref_status = []
  processed_references = set()
  discarded_ref_count = 0
  feed_collations = build_feed_collation_map(user)
  collation_url_parent_path = f"wom-user:/collation/{user.username}"
  for feed in user.userprofile.web_feeds.select_related("source").all():
    feed_references = set(feed.source.productions
                          .exclude(referenceuserstatus__owner=user).all())
    if feed in feed_collations:
      with transaction.atomic():
        feed_references = set(
          generate_collations(collation_url_parent_path,
                              feed,
                              feed_collations[feed],
                              feed_references,
                              WEB_FEED_COLLATION_MIN_NUM_REF_TARGET,
                              WEB_FEED_COLLATION_MAX_NUM_REF_TARGET,
                              WEB_FEED_COLLATION_TIMEOUT,
                              datetime.now(timezone.utc)))
    # filter out rust that have the same reference
    new_references = feed_references-processed_references
    new_ref_status += generate_reference_user_status(user,new_references)
    discarded_ref_count += len(feed_references)-len(new_references)
    processed_references.update(feed_references)
    # At least for some time, let's control the effect of the filtering
    if discarded_ref_count:
      logger.debug("Discarded {0} duplicate feed items from news feed {1}."\
                   .format(discarded_ref_count,feed.xmlURL))
  with transaction.atomic():
    for r in new_ref_status:
      r.save()
  for feed in user.userprofile.generated_feeds.select_related("source").all():
    # filter out rust that have the same reference
    feed_references = set(feed.source.productions.exclude(referenceuserstatus__owner=user).all())
    new_references = feed_references-processed_references
    new_ref_status += generate_reference_user_status(user,new_references)
    discarded_ref_count += len(feed_references)-len(new_references)
    processed_references.update(feed_references)
    # At least for some time, let's control the effect of the filtering
    if discarded_ref_count:
      logger.debug("Discarded {0} duplicate feed items from generated feed {1}."\
                   .format(discarded_ref_count,feed.title))
  with transaction.atomic():
    for r in new_ref_status:
      r.save()
  return len(new_ref_status)


@task()
def delete_obsolete_unpinned_references_from_feeds():
  for feed in WebFeed.objects.select_related("source").all():
      date_threshold = datetime.now(timezone.utc) - feed.item_relevance_duration
      feed.source.productions.filter(pin_count=0, pub_date__lt=date_threshold).delete()
  for feed in GeneratedFeed.objects.select_related("source").all():
      date_threshold = datetime.now(timezone.utc) - feed.item_relevance_duration
      feed.source.productions.filter(pin_count=0, pub_date__lt=date_threshold).delete()
