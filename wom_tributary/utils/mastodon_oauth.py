# -*- coding: utf-8; indent-tabs-mode: nil; python-indent: 2 -*-
#
# Copyright (C) 2022 Thibauld Nion
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

"""
Providing functions for the various steps described at: 
https://docs.joinmastodon.org/methods/apps/
https://docs.joinmastodon.org/methods/oauth/
"""

import urllib.request, urllib.parse, urllib.error

import logging
logger = logging.getLogger(__name__)

import requests

try:
    from granary.mastodon import Mastodon, source
    GRANARY_IMPORT_OK = True
except ImportError as e:
    # Allowing to continue on failure, will help with some weird
    # install/import issue on the CI where the actual auth is mocked
    # anyway. But the app won't work for real if that happens in
    # production.
    logging.warn(f"Failed to import granary.mastodon: {e} at module import time.")
    GRANARY_IMPORT_OK = False

CREATE_APP_PATH = '/api/v1/apps'
AUTHORIZE_PATH = '/oauth/authorize'
TOKEN_PATH = '/oauth/token'


SESSION_TOKEN_NAME = "wom_tributary_mastodon_rtk"

TIMELINE_GROUP_ID = source.FRIENDS if GRANARY_IMPORT_OK else None


class RegistrationInfo:

    DEFAULT_SCOPE = "read"

    def __init__(self, client_id, client_secret, vapid_key):
      self.client_id = client_id
      self.client_secret = client_secret
      self.vapid_key = vapid_key
      self.scope = RegistrationInfo.DEFAULT_SCOPE

    def __str__(self):
      return f"RegistrationInfo({self.client_id}, {self.client_secret}, {self.vapid_key}, {self.scope})"


def register_application_on_instance(instance_url, app_name, redirect_uri, website):
  data = {
    "client_name": app_name,
    "redirect_uris": redirect_uri,
    "scopes": RegistrationInfo.DEFAULT_SCOPE,
    "website": website
    }
  registration = requests.post(f"{instance_url.rstrip('/')}{CREATE_APP_PATH}", data=data)
  if not registration.ok:
      logger.error(f"Mastodon registration error: {registration.status_code} {registration.headers} {registration.text}")
      raise Exception(f"Failed to register the application as {app_name} on {instance_url}")
  info = registration.json()
  return RegistrationInfo(info["client_id"], info["client_secret"], info["vapid_key"])


def get_authorization_url_for_instance(instance_url, redirect_uri, registration_info):
  params = {
    "response_type": "code",
    "client_id": registration_info.client_id,
    "redirect_uri": redirect_uri,
    "scope": registration_info.scope
    }
  query_params = urllib.parse.urlencode(params)
  return f"{instance_url.rstrip('/')}{AUTHORIZE_PATH}?{query_params}"    


def get_access_token_from_instance(instance_url, redirect_uri, registration_info, code):
  data = {
    "client_id": registration_info.client_id,
    "client_secret": registration_info.client_secret,
    "redirect_uri": redirect_uri,
    "scope": registration_info.scope,
    "grant_type": "authorization_code",
    "code": code
    }
  token_response = requests.post(f"{instance_url.rstrip('/')}{TOKEN_PATH}", data=data)
  if token_response.ok:
    return token_response.json()["access_token"]
  else:
    logger.error(f"Mastodon get access token error: {token_response.status_code} {token_response.headers} {token_response.text}")
    raise Exception(f"Failed to get a token on {instance_url} {token_response.json()}")



def build_mastodon_client(instance_url, access_token):
  """Return a Granary client for Twitter."""
  if GRANARY_IMPORT_OK:
    from granary.mastodon import Mastodon as MastodonGranary
  else:
      MastodonGranary = Mastodon
  return MastodonGranary(
    instance_url,
    access_token)


def try_get_authorized_client_and_token(
    request_params,
    session,
    instance_url,
    redirect_uri,
    registration_info,
    maybe_token
    ):
  """Returns None if authorization is required, 
  and a valid client if it has been granted."""
  token = maybe_token or get_acces_token_if_present(
      request_params,
      session,
      redirect_uri,
      registration_info
      )
  if not token:
    return None
  try:
    client = build_mastodon_client(instance_url, token)
    if client and client.get_actor() is not None:
      return client, token
  except urllib.error.HTTPError as e:
    logger.warn(f"Error occured while creating the client: {e}")
    if e.code!=401: # HTTP Error 401: Authorization Required
      raise
  return None


def generate_authorization_url(session, instance_url, redirect_uri, registration_info):
  """Forges the url where the user must grant his/her authorization.
  """
  url = get_authorization_url_for_instance(instance_url, redirect_uri, registration_info)
  session[SESSION_TOKEN_NAME] = instance_url
  return url


def get_acces_token_if_present(
    request_params,
    session,
    redirect_uri,
    registration_info
    ):
  """From a request (redirected by a mastodon instance) generates the access token and save it."""
  if not request_params:
    return None
  code = request_params.get('code')
  if not code:
    return None
  instance_url = session[SESSION_TOKEN_NAME]
  if not instance_url:
    raise RuntimeError("Found a 'code' but was not expecting any.")
  del session[SESSION_TOKEN_NAME]
  return get_access_token_from_instance(instance_url, redirect_uri, registration_info, code)

