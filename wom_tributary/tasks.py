# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2019 Thibauld Nion
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
from wom_tributary.utils import mastodon_oauth
from wom_tributary.utils import tweet_summarizers

from wom_tributary.settings import SINGLE_USER_TWITTER_OAUTH_TOKEN
from wom_tributary.settings import SINGLE_USER_TWITTER_OAUTH_TOKEN_SECRET

from wom_tributary.models import TwitterTimeline, MastodonTimeline

# Wild approx of the number of tweets you can find in
# a user's home
# (that's a _very_ high bound for me but may be too short
# for some others)
APPROX_NB_TWEETS_PER_1H = 300

import logging
logger = logging.getLogger(__name__)

from html.parser import HTMLParser


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


class AuthStatus:

    def __init__(self, is_auth, client, auth_url):
      self.is_auth = is_auth
      self.client = client
      self.auth_url = auth_url


def get_twitter_auth_status(user_info, request = None):
  try:
    force_single_user_token_if_any(user_info)
    request_params, session = \
      (request.GET, request.session) if request \
      else ({},{})
    client = twitter_oauth.try_get_authorized_client(
        request_params, session, user_info)
    is_auth = client is not None
    auth_url = None if is_auth \
      else twitter_oauth.generate_authorization_url(
          session, user_info)
    return AuthStatus(is_auth, client, auth_url)
  except Exception as e:
    logging.error(f"Failed to get a proper Twitter AuthStatus because of '{e}'")
    return AuthStatus(False, None, None)


def create_reference_from_timeline_summary(
    summary, summary_url, title, date, previous_ref):
  """Takes a html summary of a timeline creates a reference from it, attributing it the publication date given in argument.

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


def add_new_reference_from_platform_timeline_summary(
    platform, timeline, summary, title, date):
  """Create and save a reference corresponding to the input.
  """
  summary_url = "wom-tributary:/{}/timeline/{}/{}".format(
    platform,
    timeline.username if hasattr(timeline, "username") else hash(timeline),
    (date - datetime.utcfromtimestamp(0)
      .replace(tzinfo=timezone.utc)).total_seconds()
    )
  same_refs = Reference.objects.filter(url=summary_url).all()
  previous_ref = same_refs[0] if same_refs else None
  r = create_reference_from_timeline_summary(
      summary,
      summary_url,
      title,
      date,
      previous_ref)
  with transaction.atomic():
    try:
      r.save()
    except Exception as e:
      logger.error(
        "Skipping news item %s because of exception: %s."\
        % (r.url,e))
      return None
  return r


def fetch_twitter_timeline_data(timeline, auth_status, max_num_items):
    if not auth_status.is_auth:
        return []
    client = auth_status.client
    tl_data = client.get_activities(
        user_id=timeline.username,
        count=max_num_items)
    return tl_data


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
    activities = fetch_twitter_timeline_data(
      timeline,
      auth,
      num_items_to_ask)
    if not activities:
      return None
    summary = tweet_summarizers.generate_basic_html_summary(
      activities,
      keep_only_after_datetime,
      tweet_summarizers.default_link_builder)
    date_str = now.strftime("%Y%m%d%H")
    title = f"{timeline.generated_feed.title} /{hours_to_cover}h"
  except Exception as e:
    logger.error("Skipping timeline for %s because of the following error: %s."\
                 % (timeline.username,e))
    return None
  r = add_new_reference_from_platform_timeline_summary(
    TwitterTimeline.SOURCE_NAME.lower(),
    timeline,
    summary,
    title,
    now
    )
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


def register_mastodon_application_info_if_needed(instance_registration_info, website_homepage):
  """Ensures the application registration info is complete.
  Requires at minimum, the following to be set in input:
  - instance_registration_info.instance_url
  - instance_registration_info.application_name

  Note: The calling code should probably lookup by itself
    if a registration was made for the same instance already
    and start building the instance_registration_info with it.
  """
  if instance_registration_info.client_secret:
    return
  app_name = instance_registration_info.application_name
  instance_url = instance_registration_info.instance_url
  redirect_uri = instance_registration_info.redirect_uri
  logger.info(f"Registering Mastodon application: '{instance_url}' '{app_name}' '{redirect_uri}' '{website_homepage}'")
  registration_feedback = mastodon_oauth.register_application_on_instance(
      instance_url,
      app_name,
      redirect_uri,
      website_homepage
      )
  instance_registration_info.client_id = registration_feedback.client_id
  instance_registration_info.client_secret = registration_feedback.client_secret
  instance_registration_info.validation_key = registration_feedback.vapid_key
  instance_registration_info.save()


def get_mastodon_auth_status(user_info, request = None):
  """Can fetch user-related tokens if they are not registered yet BUT
  assumes that user_info contains a valid application registation (see
  `register_application_on_instance` for application registration).
  """
  request_params, session = \
    (request.GET, request.session) if request \
    else ({},{})
  instance_url = user_info.application_registration_info.instance_url
  reg_info = mastodon_oauth.RegistrationInfo(
      user_info.application_registration_info.client_id,
      user_info.application_registration_info.client_secret,
      user_info.application_registration_info.validation_key,
      )
  redirect_uri = user_info.application_registration_info.redirect_uri
  maybe_token = user_info.oauth_access_token
  client, token = (
      mastodon_oauth
      .try_get_authorized_client_and_token(
        request_params,
        session,
        instance_url,
        redirect_uri,
        reg_info,
        maybe_token
        ) or (None, None))
  is_auth = client is not None
  if is_auth:
    user_info.oauth_access_token = token
    user_info.save()
  auth_url = None if is_auth \
    else mastodon_oauth.generate_authorization_url(
        request.session,
        instance_url,
        redirect_uri,
        reg_info)
  return AuthStatus(is_auth, client, auth_url)


def fetch_mastodon_timeline_data(timeline, auth_status, max_num_items):
    if not auth_status.is_auth:
        return []
    client = auth_status.client
    tl_data = client.get_activities(
        group_id=mastodon_oauth.TIMELINE_GROUP_ID,
        count=max_num_items)
    return tl_data


class MastodonLinkBuilder:

  def __init__(self, instance_url):
    self.instance_url = instance_url

  def __call__(self, activity_item):
    actor_instance_path = "@".join(
        activity_item
        .get("actor", {})
        .get("id", "")
        .split(":")[:0:-1]
        )
    item_id = (
        activity_item
        .get("object", {})
        .get("id", ":")
        .split(":")[-1]
        )
    if actor_instance_path and item_id:
      return f"{self.instance_url}/@{actor_instance_path}/{item_id}"
    return tweet_summarizers.default_link_builder(activity_item)


def collect_new_references_for_mastodon_timeline(
    timeline,
    hours_to_cover):
  """Get the timeline data from Mastodon and collect the new references into the db.
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
  access_info = timeline.mastodon_user_access_info
  try:
    auth = get_mastodon_auth_status(access_info)
    activities = fetch_mastodon_timeline_data(
      timeline,
      auth,
      num_items_to_ask)
    if not activities:
      return None
    summary = tweet_summarizers.generate_basic_html_summary(
      activities,
      keep_only_after_datetime,
      MastodonLinkBuilder(timeline.mastodon_user_access_info.application_registration_info.instance_url))
    date_str = now.strftime("%Y%m%d%H")
    title = f"{timeline.generated_feed.title} /{hours_to_cover}h"
  except Exception as e:
    logger.error("Skipping timeline for %s because of the following error: %s."\
                 % (feed.title, e))
    return None
  r = add_new_reference_from_platform_timeline_summary(
    MastodonTimeline.SOURCE_NAME.lower(),
    timeline,
    summary,
    title,
    now
    )
  r.sources.add(timeline.generated_feed.source)
  r.save()
  feed.last_update_check = now
  feed.save()
  return r


def collect_news_from_mastodon_feeds(hours_to_cover):
  """Fetch toots for the given info and fill the db of
  References with them.

  This is to ensure that we don't try
  """
  for timeline in MastodonTimeline.objects.iterator():
    collect_new_references_for_mastodon_timeline(
      timeline, hours_to_cover)

