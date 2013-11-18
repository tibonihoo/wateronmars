# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-

from wom_river.utils.netscape_bookmarks import parse_netscape_bookmarks

from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import Reference

from celery import task

from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

import datetime
from urlparse import urlparse
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)


def build_reference_title_from_url(url):
  """Generate a valid reference title from an url.
  Mostly remove the protocol part of an url wih a few additional safety tricks.
  """
  url_cpt = urlparse(url)
  reference_title = url_cpt.hostname or ""
  if url_cpt.path.split("/") and url_cpt.path != "/":
    reference_title +=  url_cpt.path
  return reference_title


def truncate_reference_title(title):
  """Implement a default strategy to make sure that a reference title
  enforces the maimum length constraint for the Reference model.
  """
  if len(title)>REFERENCE_TITLE_MAX_LENGTH:
    return title[:REFERENCE_TITLE_MAX_LENGTH-3] + "..." 
  else:
    return title

def build_source_url_from_reference_url(ref_url):
  """Generate a url that could realistically by considered as the source
  of the given url.
  """
  url_cpt = urlparse(ref_url)
  if url_cpt.scheme:
    prefix = url_cpt.scheme+"://"
  else:
    prefix = ""
  return (prefix+url_cpt.netloc) or ref_url

  
# A common structure to be returned by functions that import reference
# instance from bookmark list.
BookmarkMetadata = namedtuple("BookmarkMetadata",'note, tags, is_public')

@task()
def import_references_from_ns_bookmark_list(nsbmk_txt):
  """Extract bookmarks from a Netscape-style bookmark file and save
  them as Reference instances in the database.
  
  nsbmk_txt: a unicode string representing the full content of a
  Netscape-style bookmark file.

  Return a dictionary mapping each reference with the BookmarkMetadata
  associated to it according to the input content.
  """
  date_now = datetime.datetime.now(timezone.utc)
  # Parse the file
  collected_bmks = parse_netscape_bookmarks(nsbmk_txt)
  if not collected_bmks:
    return {}
  # Make sure that the source common to all the following import
  # exists or create it to be able to link new references to it.
  source_url = "internal://bookmark-import-nsbmk"
  try:
    common_source = Reference.objects.get(url=source_url)
  except ObjectDoesNotExist:
    common_source = Reference(url=source_url,
                              title="Bookmark Import (Netscape-style bookmarks)",
                              pub_date=date_now)
    common_source.save()
  new_refs  = []
  ref_and_metadata = []
  for bmk_info in collected_bmks:
    u = bmk_info["url"]
    info = ""
    if len(u)>URL_MAX_LENGTH:
      # WOM should be configured in such a way that this never happens !
      truncation_txt = "<wom truncation>"
      # Save the full url in info to limit the loss of information
      info = u"<WOM had to truncate the following URL: %s>" % u
      logger.warning("Found an url of length %d (>%d) \
when importing Netscape-style bookmark list." % (len(u),URL_MAX_LENGTH))
      u = u[:URL_MAX_LENGTH-len(truncation_txt)]+truncation_txt
    t = bmk_info.get("title") or build_reference_title_from_url(u)
    if "posix_timestamp" in bmk_info:
      d = datetime.datetime\
                  .utcfromtimestamp(float(bmk_info["posix_timestamp"]))\
                  .replace(tzinfo=timezone.utc)
    else:
      d = date_now
    try:
      ref = Reference.objects.get(url=u)
    except ObjectDoesNotExist:
      ref = Reference(url=u,title=truncate_reference_title(t),
                      pub_date=d,description=info)
      new_refs.append(ref)
    meta = BookmarkMetadata(bmk_info.get("note",""),
                            set(bmk_info.get("tags","").split(",")),
                            bmk_info.get("private","0")=="0")
    ref_and_metadata.append((ref,meta))
  with transaction.commit_on_success():
    for ref in new_refs:
      ref.save()
      ref.sources.add(common_source)
  # Note: We have to wait until now to convert the list to a dict,
  # because only now will the model instances have their specific ids and
  # hashes (before that they would have looked the same for the dict).
  return dict(ref_and_metadata)

