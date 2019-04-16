# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright 2019 Thibauld Nion
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

from datetime import timedelta
from datetime import datetime
from django.utils import timezone
from django.db import transaction

from wom_pebbles.models import Reference

from wom_pebbles.tasks import truncate_reference_title
from wom_pebbles.tasks import sanitize_url

from wom_tributary.utils import twitter_oauth
from wom_tributary.utils import tweet_summarizers

from wom_tributary.settings import SINGLE_USER_TWITTER_OAUTH_TOKEN
from wom_tributary.settings import SINGLE_USER_TWITTER_OAUTH_TOKEN_SECRET

from wom_tributary.models import TwitterTimeline

# Wild approx of the number of tweets you can find in
# a user's home
# (that's a _very_ high bound for me but may be too short
# for some others)
APPROX_NB_TWEETS_PER_1H = 300

import logging
logger = logging.getLogger(__name__)

from HTMLParser import HTMLParser


def HTMLUnescape(s):
  return HTMLParser().unescape(s)


def force_single_user_token_if_any(user_info):
  if not user_info:
    None
  su_tk = SINGLE_USER_TWITTER_OAUTH_TOKEN
  su_st = SINGLE_USER_TWITTER_OAUTH_TOKEN_SECRET
  if None in (su_tk, su_st):
    return
  user_info.oauth_access_token = su_tk
  user_info.oauth_access_token_secret = su_st
  user_info.save()


class TwitterAuthStatus:

    def __init__(self, is_auth, client, auth_url):
      self.is_auth = is_auth
      self.client = client
      self.auth_url = auth_url

def get_twitter_auth_status(user_info, request = None):
  force_single_user_token_if_any(user_info)
  request_params, session = \
    (request.GET, request.session) if request \
    else ({},{})
  client = twitter_oauth.try_get_authorized_client(
    request_params, session, user_info)
  is_auth = client is not None
  auth_url = None if is_auth \
    else twitter_oauth.generate_authorization_url(
        request.session, user_info)
  return TwitterAuthStatus(is_auth, client, auth_url)


def fetch_timeline_data(timeline, auth_status, max_num_items):
    if not auth_status.is_auth:
        return []
    client = auth_status.client
    tl_data = client.get_activities(
        user_id=timeline.username,
        count=max_num_items)
    return tl_data


def create_reference_from_tweet_summary(
    summary, summary_url, title, date, previous_ref):
  """Takes a html summary of a tweet timeline creates a reference from it, attributing it the publication date given in argument.

  If the corresponding Reference already exists, it must be given as
  the previous_ref argument, and if previous_ref is None, it will be
  assumed that there is no matching Rerefence in the db.
  
  Return a tuple with the unsaved reference and a list of tag names.
  """
  if previous_ref is None:
    url_truncated, did_truncate = sanitize_url(summary_url)
    assert not did_truncate
    title_truncated = truncate_reference_title(title)
    ref = Reference(url=summary_url,title=title_truncated)
  else:
    ref = previous_ref
  ref.description = summary
  ref.pub_date = date
  return ref


def add_new_reference_from_tweeter_timeline_summary(
    timeline, summary, title, date):
  """Create and save a reference corresponding to the input.
  """
  summary_url = "wom-tributary:/twitter/timeline/{}/{}".format(
    timeline.username,
    (date - datetime.utcfromtimestamp(0)
      .replace(tzinfo=timezone.utc)).total_seconds()
    )
  same_refs = Reference.objects.filter(url=summary_url).all()
  previous_ref = same_refs[0] if same_refs else None
  r = create_reference_from_tweet_summary(
      summary,
      summary_url,
      title,
      date,
      previous_ref)
  with transaction.commit_on_success():
    try:
      r.save()
    except Exception,e:
      logger.error(
        "Skipping news item %s because of exception: %s."\
        % (r.url,e))
      return None
  return r


def collect_new_references_for_twitter_timeline(
    timeline,
    hours_to_cover):
  """Get the timeline data from Twitter and collect the new references into the db.
  Return a dictionary mapping the new references to a corresponding set of tags.
  """  
  feed = timeline.generated_feed
  now = timezone.now()
  last_update_check = feed.last_update_check
  if last_update_check >= now:
    return None
  num_items_to_ask = APPROX_NB_TWEETS_PER_1H * hours_to_cover
  earliest_item_date_allowed = (
    now - timedelta(hours=hours_to_cover)
    )
  keep_only_after_datetime = max(last_update_check, earliest_item_date_allowed)
  access_info = timeline.twitter_user_access_info
  try:
    auth = get_twitter_auth_status(access_info)
    activities = fetch_timeline_data(
      timeline,
      auth,
      num_items_to_ask)
    summary = tweet_summarizers.generate_basic_html_summary(
      activities,
      keep_only_after_datetime)
    date_str = now.strftime("%Y%m%d%H")
    title = "{}/{}h {}".format(
      date_str,
      hours_to_cover,
      timeline.generated_feed.title)
  except Exception,e:
    logger.error("Skipping timeline for %s because of the following error: %s."\
                 % (timeline.username,e))
    return None
  r = add_new_reference_from_tweeter_timeline_summary(
    timeline, summary, title, now)
  r.sources.add(timeline.generated_feed.source)
  r.save()
  feed.last_update_check = now
  feed.save()
  return r


def collect_news_from_tweeter_feeds(hours_to_cover):
  """Fetch tweets for the given info and fill the db of
  References with them.

  This is to ensure that we don't try
  """
  for timeline in TwitterTimeline.objects.iterator():
    collect_new_references_for_twitter_timeline(
      timeline, hours_to_cover)

