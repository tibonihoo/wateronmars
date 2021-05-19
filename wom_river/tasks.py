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

import feedparser
from bs4 import BeautifulSoup

from datetime import datetime
from django.utils import timezone
from django.utils.html import strip_tags

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import MultipleObjectsReturned

from wom_pebbles.models import Reference, build_safe_code_from_url

from wom_river.models import WebFeed
from wom_river.utils.read_opml import parse_opml

from wom_pebbles.models import URL_MAX_LENGTH

from wom_pebbles.tasks import truncate_reference_title
from wom_pebbles.tasks import sanitize_url


import logging
logger = logging.getLogger(__name__)

import html

def HTMLUnescape(s):
  return html.unescape(s)


def get_date_from_feedparser_entry(entry):
  """
  Extract the date from the 'parsed date' fields of a feedparser generated entry.
  """
  if "updated_parsed" in entry:
    updated_date_utc = entry.updated_parsed[:6]
  elif "published_parsed" in entry:
    updated_date_utc = entry.published_parsed[:6]
  elif "created_parsed" in entry:
    updated_date_utc = entry.created_parsed[:6]
  else:
    logger.debug("Using 'now' as date for item %s" % entry.link)
    updated_date_utc = datetime.now(timezone.utc).utctimetuple()[:6]
  return datetime(*(updated_date_utc),tzinfo=timezone.utc)


def create_reference_from_feedparser_entry(entry,date,previous_ref):
  """Takes a FeedParser entry and create a reference from it and
  attributing it the publication date given in argument.

  If the corresponding Reference already exists, it must be given as
  the previous_ref argument, and if previous_ref is None, it will be
  assumed that there is no matching Rerefence in the db.

  Note: Enforce Dave Winer's recommendation for linkblog:
  http://scripting.com/2014/04/07/howToDisplayTitlelessFeedItems.html
  with a little twist: if a feed item has no title we will use the
  (possibly truncated) description as a title and if there is no
  description the link will be used. In any case the description of a
  reference is set even if this description is also used for the
  title.
  
  Return a tuple with the unsaved reference and a list of tag names.
  """
  url = entry.link
  info = ""
  tags = set()
  if entry.get("tags",None):
    tags = set([t.term for t in entry.tags])
  if previous_ref is None:
    url_truncated,did_truncate = sanitize_url(url)
    if did_truncate:
      # Save the full url in info to limit the loss of information
      info = "<WOM had to truncate the following URL: %s>" % url
      logger.warning("Found an url of length %d (>%d) \
when importing references from feed." % (len(url),URL_MAX_LENGTH))
    url = url_truncated
    # set the title only for new ref (should avoid weird behaviour
    # from the user point of view)
    title = truncate_reference_title(
      HTMLUnescape(entry.get("title") \
                   or strip_tags(entry.get("description")) \
                   or url))
    ref = Reference(url=url,title=title)
  else:
    ref = previous_ref
  ref.description = " ".join((info,entry.get("description","")))
  ref.pub_date = date
  return (ref,tags)


def add_new_references_from_feedparser_entries(feed,entries):
  """Create and save references from the entries found in a feedparser
  generated list.
  
  Returns a dictionary mapping the saved references to the tags that are
  associated to them in the feed.
  """
  common_source = feed.source
  feed_last_update_check = feed.last_update_check
  latest_item_date = feed_last_update_check
  all_references = []
  ref_by_url = {}
  entries_with_link = []
  # reject entries that have no link tag
  for e in entries:
    entry_link = e.get("link",None)
    if not entry_link:
      logger.warning("Skipping a feed entry without 'link' : %s." % e)
      continue
    entries_with_link.append(e)
  entries_with_dates = [(e,get_date_from_feedparser_entry(e)) for e in entries_with_link]
  new_entries = [(e,d) for e,d in entries_with_dates \
                 if d>feed_last_update_check]
  entries_url = [e.link for e,_ in new_entries if e.get("link",None)]
  existing_references = list(Reference.objects.filter(url__in=entries_url).all())
  existing_references_by_url = dict([(r.url,r) for r in existing_references])
  for entry,date in new_entries:
    entry_link = entry.link
    previous_ref = existing_references_by_url.get(entry_link,None)
    if previous_ref is None:
      # there may also be duplicate in the current feed list of items
      previous_ref = ref_by_url.get(entry_link,None)
    r,tags = create_reference_from_feedparser_entry(entry,date,previous_ref)
    ref_by_url[r.url] = r
    current_ref_date = r.pub_date
    all_references.append((r,tags))
    if current_ref_date > latest_item_date:
      latest_item_date = current_ref_date
  # save all references at once
  with transaction.atomic():
    for r,_ in all_references:
      try:
        r.save()
      except Exception as e:
        logger.error("Skipping news item %s because of exception: %s."\
                     % (r.url,e))
        continue
      r.sources.add(common_source)
  feed.last_update_check = latest_item_date
  feed.save()
  return dict(all_references)


def collect_new_references_for_feed(feed):
  """Get the feed data from its URL and collect the new references into the db.
  Return a dictionary mapping the new references to a corresponding set of tags.
  """
  try:
    d = feedparser.parse(feed.xmlURL)
  except Exception as e:
    logger.error("Skipping feed at %s because of a parse problem (%s))."\
                 % (feed.source.url,e))
    return []
  return add_new_references_from_feedparser_entries(feed,d.entries)



def collect_news_from_feeds():
  """Fetch and parse all feeds to collect new items and fill the db of
  References with them.
  """
  for feed in WebFeed.objects.iterator():
    collect_new_references_for_feed(feed)


def import_feedsources_from_opml(opml_txt):
  """
  Save in the db the FeedSources found in the OPML-formated text.
  opml_txt: a unicode string representing the content of a full OPML file.
  Return a dictionary assiociating each feed with a set of tags {feed:tagSet,...).
  """
  collected_feeds,_ = parse_opml(opml_txt,False)
  db_new_feedsources = []
  feeds_and_tags = []
  newly_referenced_source = []
  for current_feed in collected_feeds:
    try:
      feed_source = WebFeed.objects.get(xmlURL=current_feed.xmlUrl)
    except MultipleObjectsReturned:
      feed_source = WebFeed.objects.all()[0]
    except ObjectDoesNotExist:
      url_id = current_feed.htmlUrl or current_feed.xmlUrl
      try:
        ref = Reference.objects.get(url=url_id)
      except ObjectDoesNotExist:
        ref = Reference(url=url_id,title=HTMLUnescape(current_feed.title),
                        pub_date=datetime.now(timezone.utc))
        ref.save()
      feed_source = WebFeed(source=ref,xmlURL=current_feed.xmlUrl)
      feed_source.last_update_check = datetime.utcfromtimestamp(0)\
                                              .replace(tzinfo=timezone.utc)
      newly_referenced_source.append(ref)
      db_new_feedsources.append(feed_source)
    feeds_and_tags.append((feed_source,current_feed.tags))
  with transaction.atomic():
    for f in db_new_feedsources:
      f.save()
    for r in newly_referenced_source:
      r.add_pin()
      r.save()
  return dict(feeds_and_tags)


def generate_collated_content(references):
  doc_lines = []
  for ref in references:
    doc_lines.append(f"<h2><a href='{ref.url}'>{ref.title}</a></h2>")
    # Due to the accumulation of possibly flacky content, it's better
    # to prettify piece by piece (it did happen that prettifying the
    # whole collation in one go broke beautifulsoup in the case when
    # each description only contained a <p> without ever closing it.)
    soup = BeautifulSoup(ref.description, 'html.parser')
    doc_lines.append(soup.prettify())
    doc_lines.append("<br/>")
  return "\n".join(doc_lines)


def format_date_extent(delta):
  days = delta.days
  hours = delta.seconds // 3600
  if days:
    displayed_days = days+1 if hours >= 6 else days
    return f"{displayed_days}d"
  minutes = (delta.seconds // 60) - (hours * 60)
  if hours:
    displayed_hours = hours+1 if minutes >= 15 else hours
    return f"{displayed_hours}h"
  displayed_minutes = max(1, minutes//60)
  return f"{displayed_minutes}min"


def yield_collated_reference(url_parent_path, feed, feed_collation,
                             min_num_ref_target,
                             timeout, processing_date):
  references = list(feed_collation.references.order_by('pub_date').all())
  num_refs = len(references)
  if num_refs == 0:
    return
  age = (processing_date
         - feed_collation.last_completed_collation_date)
  num_refs_cap = 100*min_num_ref_target
  num_refs_below_cap = num_refs < num_refs_cap
  if age < timeout and num_refs_below_cap:
    return
  processed_references = references[:num_refs_cap]
  if num_refs_cap < num_refs:
    logger.warning(f"Collated references list cropped from {num_refs} to {num_refs_cap}")
  earliest_pub_date = processed_references[0].pub_date
  most_recent_pub_date = processed_references[-1].pub_date
  date_extent = most_recent_pub_date - earliest_pub_date
  too_few_refs = num_refs < min_num_ref_target
  young_enough = age < 1.5*timeout
  if too_few_refs and young_enough and num_refs_below_cap:
    return
  source = feed.source
  source_url_code = source.url
  feed_url_code = build_safe_code_from_url(feed.xmlURL)
  pub_date = processing_date
  url = "{}/{}/{}/{}/{}".format(
      url_parent_path,
      source_url_code,
      feed_url_code,
      (pub_date - datetime.utcfromtimestamp(0)
       .replace(tzinfo=timezone.utc)).total_seconds(),
      (earliest_pub_date - datetime.utcfromtimestamp(0)
       .replace(tzinfo=timezone.utc)).total_seconds())
  same_refs = Reference.objects.filter(url=url).all()
  if same_refs:
    logger.warning(f"Skipped duplicated collated reference for {url}")
    return
  description = generate_collated_content(processed_references)
  date_extent_str = format_date_extent(date_extent)
  t = f"{source.title} /{date_extent_str}"
  r = Reference(url=url,
                title=t,
                pub_date=pub_date,
                description=description)
  r.save()
  r.sources.add(source)
  feed_collation.flush(processing_date)
  feed_collation.save()
  yield r



def generate_collations(url_parent_path,
                        feed, feed_collation, feed_references,
                        min_num_ref_target, timeout, processing_date):
  for ref in feed_references:
    yield from yield_collated_reference(url_parent_path, feed, feed_collation, min_num_ref_target, timeout, processing_date)
    feed_collation.take(ref)
  else:
    yield from yield_collated_reference(url_parent_path, feed, feed_collation, min_num_ref_target, timeout, processing_date)
