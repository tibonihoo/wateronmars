# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2013 Thibauld Nion
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

from django.utils.encoding import iri_to_uri

from wom_river.utils.netscape_bookmarks import parse_netscape_bookmarks

from wom_pebbles.models import REFERENCE_TITLE_MAX_LENGTH
from wom_pebbles.models import URL_MAX_LENGTH
from wom_pebbles.models import Reference


from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

import datetime
from urlparse import urlparse
from collections import namedtuple

import logging
logger = logging.getLogger(__name__)

import re

# A string defining the query string related to "campain" trackers,
# that may end up being stripped out when a url is too long.
URL_CAMPAIN_QS_RE = re.compile("utm_[^&]*(&|$)")

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
    # use space aware cut recommended at http://stackoverflow.com/questions/250357/truncate-a-string-without-ending-in-the-middle-of-a-word
    return title[:REFERENCE_TITLE_MAX_LENGTH-3].rsplit(' ',1)[0] + "..."
  else:
    return title


def sanitize_url(url):
  """Quote non-ascii characters and spaces and truncate a URL to make
  sure it enforces the URL_MAX_LENGTH constraint.
  
  Returns a tuple: (new_url,did_truncate) where new_url is either the
  input url or its truncated version and did_truncate is True iff the
  url has to be truncated.
  """
  # Check encoding and make sure that URL are 
  url = iri_to_uri(url)
  # WOM should be configured in such a way that this never happens !
  if len(url)<=URL_MAX_LENGTH:
    return url,False
  url = URL_CAMPAIN_QS_RE.sub("",url)
  if len(url)>URL_MAX_LENGTH:
    truncation_txt = "#wom_truncation#"
    url = url[:URL_MAX_LENGTH-len(truncation_txt)]+truncation_txt
  return url,True

    
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
  source_url = "#internal-bookmark-import"
  try:
    common_source = Reference.objects.get(url=source_url)
  except ObjectDoesNotExist:
    common_source = Reference(url=source_url,
                              title="Bookmark Import",
                              pub_date=date_now)
    common_source.save()
  new_refs  = []
  ref_and_metadata = []
  new_ref_by_url = {}
  for bmk_info in collected_bmks:
    u = bmk_info["url"]
    if not u:
      logger.warning("Skipping a bookmark that has an empty URL.")
      continue
    info = ""
    u_truncated, did_truncate = sanitize_url(u)
    if did_truncate:
      # Save the full url in info to limit the loss of information
      info = u"<WOM had to truncate the following URL: %s>" % u
      logger.warning("Found an url of length %d (>%d) \
when importing Netscape-style bookmark list." % (len(u),URL_MAX_LENGTH))
    u = u_truncated
    t = bmk_info.get("title") or build_reference_title_from_url(u)
    if "posix_timestamp" in bmk_info:
      d = datetime.datetime\
                  .utcfromtimestamp(float(bmk_info["posix_timestamp"]))\
                  .replace(tzinfo=timezone.utc)
    else:
      d = date_now
    if u in new_ref_by_url:
      ref = new_ref_by_url[u]
    else:
      try:
        ref = Reference.objects.get(url=u)
      except ObjectDoesNotExist:
        ref = Reference(url=u,title=truncate_reference_title(t),
                        pub_date=d,description=info)
        new_refs.append(ref)
        new_ref_by_url[u] = ref
    meta = BookmarkMetadata(bmk_info.get("note",""),
                            set(bmk_info.get("tags","").split(",")),
                            bmk_info.get("private","0")=="0")
    ref_and_metadata.append((ref,meta))
  with transaction.atomic():
    for ref in new_refs:
      ref.save()
      ref.sources.add(common_source)
  # Note: We have to wait until now to convert the list to a dict,
  # because only now will the model instances have their specific ids and
  # hashes (before that they would have looked the same for the dict).
  return dict(ref_and_metadata)

def delete_old_unpinned_references(time_threshold):
  """Delete references that are older that the time_threshold and have a
  save count equal to 0.
  """
  Reference.objects.filter(pin_count=0,pub_date__lt=time_threshold).delete()
