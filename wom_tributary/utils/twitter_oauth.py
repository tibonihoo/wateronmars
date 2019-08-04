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

"""
Providing functions for the various steps described at: 
https://developer.twitter.com/en/docs/basics/authentication/overview/3-legged-oauth.html
"""

import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import tweepy
from granary.twitter import Twitter
from granary.twitter import appengine_config as twitter_cfg

SESSION_TOKEN_NAME = "wom_tributary_twitter_rtk"

def build_twitter_client(user_info):
  """Return a Granary client for Twitter."""
  return Twitter(
    user_info.oauth_access_token,
    user_info.oauth_access_token_secret,
    user_info.username)

def try_get_authorized_client(
    request_params, session, user_info):
  """Returns None if authorization is required, 
  and a valid client if it has been granted."""
  register_acces_token_if_present(
    request_params, session, user_info)
  if not user_info.oauth_access_token \
    or not user_info.oauth_access_token_secret:
    return None
  try:
    client = build_twitter_client(user_info)
    if client and client.get_actor() is not None:
      return client
  except urllib.error.HTTPError as e:
    if e.code!=401: # HTTP Error 401: Authorization Required
      raise
  except urllib.error.HTTPError as e:
    if e.code!=401: # HTTP Error 401: Authorization Required
      raise
  return None


def generate_authorization_url(session, user_info):
  """Performs "step1" of the 3-leg auth by collecting a session token 
  and forging the url where the user must grant his/her authorization.
  """
  app_key, app_secret = get_consumer_app_key()
  auth = tweepy.OAuthHandler(app_key, app_secret)
  redirect_url = auth.get_authorization_url(
    signin_with_twitter=True
    )
  session[SESSION_TOKEN_NAME] = auth.request_token
  return redirect_url


def register_acces_token_if_present(
    request_params, session, user_info):
  """From a request (redirected by Twitter) generates the access token and save it."""
  if not request_params:
    return
  verifier = request_params.get('oauth_verifier')
  if not verifier:
    return
  request_token = session[SESSION_TOKEN_NAME]
  if not request_token:
    raise RuntimeError("Found an oauth_verifier but was not expecting any.")
  del session[SESSION_TOKEN_NAME]
  app_key, app_secret = get_consumer_app_key()
  auth = tweepy.OAuthHandler(app_key, app_secret)
  auth.request_token = request_token
  auth.get_access_token(verifier)
  user_info.oauth_access_token = auth.access_token
  user_info.oauth_access_token_secret = auth.access_token_secret
  user_info.save()

def get_consumer_app_key():
  # See https://github.com/snarfed/oauth-dropins
  # (used by granary) for how this is fetched.
  key = twitter_cfg.TWITTER_APP_KEY
  secret = twitter_cfg.TWITTER_APP_SECRET
  return key, secret
