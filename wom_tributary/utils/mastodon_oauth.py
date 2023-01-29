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
import requests
from granary.mastodon import Mastodon, source


CREATE_APP_PATH = '/api/v1/apps'
VERIFY_APP_PATH = '/api/v1/accounts/verify_credentials'
AUTHORIZE_PATH = '/oauth/authorize'
TOKEN_PATH = '/oauth/token'


SESSION_TOKEN_NAME = "wom_tributary_mastodon_rtk"

TIMELINE_GROUP_ID = source.FRIENDS


class RegistrationInfo:

    DEFAULT_SCOPE = "read"

    def __init__(self, client_id, client_secret, vapid_key, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.vapid_key = vapid_key
        self.redirect_uri = redirect_uri
        self.scope = RegistrationInfo.DEFAULT_SCOPE


def register_application_on_instance(instance_url, app_name, redirect_uri, website):
  data = {
    "client_name": app_name,
    "redirect_uris": redirect_uri,
    "scopes": RegistrationInfo.DEFAULT_SCOPE,
    "website": website
    }
  registration = requests.post(f"{instance_url}{CREATE_APP_PATH}", data=data)
  if not registration.ok:
      raise Exception(f"Failed to register the application as {app_name} on {instance_url}")
  info = registration.json()
  return RegistrationInfo(info["client_id"], info["client_secret"], info["vapid_key"], redirect_uri)


def is_application_registration_ok_on_instance(instance_url, registration_info):
  params = {
    "client_id": registration_info.client_id,
    "client_secret": registration_info.client_secret
  }
  validation = requests.get(f"{instance_url}{VERIFY_APP_PATH}", params=params)
  return validation.ok


def get_authorization_url_for_instance(instance_url, registration_info):
  params = {
    "client_id": registration_info.client_id,
    "redirect_uri": registration_info.redirect_uri,
    "scope": registration_info.scope
    }
  query_params = urllib.parse.urlencode(params)
  return f"{instance_url}{AUTHORIZE_PATH}?{query_params}"    


def get_access_token_from_instance(instance_url, registration_info, code):
  data = {
    "client_id": registration_info.client_id,
    "cient_secret": registration_info.client_secret,
    "redirect_uri": registration_info.redirect_uri,
    "scope": registration_info.scope,
    "grant_type": "authorization_code",
    "code": code
    }
  token_response = requests.post(f"{instance_url}{TOKEN_PATH}", data=data)
  if token_response.ok:
    return token_response.json()["access_token"]
  else:
    raise Exception("Failed to get a token on {instance_url} {token_response.json()}")



def build_mastodon_client(instance_url, access_token):
  """Return a Granary client for Twitter."""
  return Mastodon(
    instance_url,
    access_token)


def try_get_authorized_client_and_token(
    request_params,
    session,
    instance_url,
    registration_info
    ):
  """Returns None if authorization is required, 
  and a valid client if it has been granted."""
  token = get_acces_token_if_present(
      request_params,
      session,
      registration_info
      )
  if not token:
    return None
  try:
    client = build_mastodon_client(instance_url, token)
    if client and client.get_actor() is not None:
      return client, token
  except urllib.error.HTTPError as e:
    if e.code!=401: # HTTP Error 401: Authorization Required
      raise
  return None


def generate_authorization_url(session, instance_url, registration_info):
  """Forges the url where the user must grant his/her authorization.
  """
  url = get_authorization_url_for_instance(instance_url, registration_info, redirect_uri, scope)
  session[SESSION_TOKEN_NAME] = instance_url
  return url


def get_acces_token_if_present(
    request_params,
    session,
    registration_info
    ):
  """From a request (redirected by a mastodon instance) generates the access token and save it."""
  if not request_params:
    return None
  code = request_params.get('code')
  if not verifier:
    return None
  instance_url = session[SESSION_TOKEN_NAME]
  if not instance_url:
    raise RuntimeError("Found a 'code' but was not expecting any.")
  del session[SESSION_TOKEN_NAME]
  return get_access_token_from_instance(instance_url, registration_info, code)

