# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from datetime import datetime
from django.utils import timezone

from celery.task.schedules import crontab  
from celery.decorators import periodic_task  
from celery.decorators import task  


from wom_pebbles.tasks import delete_old_references
from wom_pebbles.tasks import import_references_from_ns_bookmark_list

from wom_river.tasks import collect_news_from_feeds
from wom_river.tasks import import_feedsources_from_opml

from wom_user.settings import NEWS_TIME_THRESHOLD

from wom_pebbles.models import Reference
from wom_user.models import UserBookmark
from wom_user.models import UserProfile
from wom_user.models import ReferenceUserStatus

from wom_classification.models import TAG_NAME_MAX_LENGTH
from wom_classification.models import set_item_tag_names

import logging
logger = logging.getLogger(__name__)

# Tasks to be run regularly.
# http://celeryproject.org/docs/reference/celery.task.schedules.html#celery.task.schedules.crontab


@periodic_task(run_every=crontab(hour="*", minute="*/20", day_of_week="*"))
def collect_all_new_references_regularly():
  collect_news_from_feeds()


@periodic_task(run_every=crontab(hour="*/12", day_of_week="*"))
def delete_old_references_regularly():
  delete_old_references(NEWS_TIME_THRESHOLD)


@task()
def import_user_bookmarks_from_ns_list(user,nsbmk_txt):
  ref_and_metadata = import_references_from_ns_bookmark_list(nsbmk_txt)
  bmk_to_save = []
  for ref,meta in ref_and_metadata.items():
    try:
      bmk = UserBookmark.objects.get(owner=user,reference=ref)
    except ObjectDoesNotExist:
      bmk = UserBookmark(owner=user,reference=ref,
                         saved_date=datetime.now(timezone.utc))    
    bmk_to_save.append((bmk,meta))
  with transaction.commit_on_success():
    for b,_ in bmk_to_save:
      b.save()
  classif_data_to_save = []
  for bmk,meta in bmk_to_save:
    valid_tags = [t for t in meta.tags if len(t)<=TAG_NAME_MAX_LENGTH]
    if len(valid_tags)!=len(meta.tags):
      invalid_tags = [t for t in meta.tags if len(t)>TAG_NAME_MAX_LENGTH]
      logger.error("Could not import some bmk tags with too long names (%s>%s)"\
                   % (",".join(len(t) for t in invalid_tags),TAG_NAME_MAX_LENGTH))
    classif_data_to_save.append(set_item_tag_names(user,bmk.reference,valid_tags))
  with transaction.commit_on_success():
    for cd in classif_data_to_save:
      cd.save()
  # TODO take into account private bmks !
  # TODO set a user-description
  # TODO add a tag in a new tag list of the user profile


@task()
def import_user_feedsources_from_opml(user,opml_txt):
  feeds_and_tags = import_feedsources_from_opml(opml_txt)
  profile = UserProfile.objects.get(user=user)
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
    classif_data_to_save.append(set_item_tag_names(user,feed,tags))
  with transaction.commit_on_success():
    for cd in classif_data_to_save:
      cd.save()
  # TODO add a tag in a new tag list of the user profile


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
      rust.reference = ref
      rust.reference_pub_date = ref.pub_date
      try:
        rust.main_source = ref.sources.filter(userprofile=user.userprofile).distinct().order_by("pub_date").get()
      except ObjectDoesNotExist:
        try:
          rust.main_source = Reference.objects.get(url="<unknown>")
        except ObjectDoesNotExist:
          s = Reference(url="<unknown>",title="<unknown>",
                        pub_date=datetime.utcfromtimestamp(0)\
                        .replace(tzinfo=timezone.utc))
          s.save()
          rust.main_source = s
      new_ref_status.append(rust)
      # TODO: check here that the corresponding reference has not
      # been saved already !
    elif user is None:
      rust = FakeReferenceUserStatus()
      rust.reference = ref
      rust.reference_pub_date = ref.pub_date
      new_ref_status.append(rust)      
  return new_ref_status


@task()  
def check_user_unread_feed_items(user):
  """
  Browse all feed sources registered by a given user and create as
  many UnreadReferenceByUser instances as there are unread items.
  """
  new_ref_status = []
  for feed in user.userprofile.web_feeds.select_related("source").all():
    new_ref_status += generate_reference_user_status(user,
                                                     feed.source\
                                                     .productions.all()\
                                                     .select_related("referenceuserstatus_set"))
  with transaction.commit_on_success():
    for r in new_ref_status:
      r.save()

