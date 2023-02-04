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

import mock

from datetime import datetime
from django.utils import timezone

from django.urls import reverse

from django.test import TestCase

from wom_pebbles.models import Reference

from wom_user.models import UserProfile

from wom_tributary.models import (
    MastodonTimeline,
    GeneratedFeed,
    MastodonUserAccessInfo,
    MastodonApplicationRegistration,
    )
from wom_tributary.utils.mastodon_oauth import RegistrationInfo


from django.contrib.auth.models import User

DEFAULT_INSTANCE = "http://mastodon.example.com"
MOCK_CLIENT_ID = "mock_client_id"
MOCK_CLIENT_SECRET = "mock_client_secret"
MOCK_VAPID_KEY = "mock_vapid_key"
MOCK_SCOPE = "mock_scope"
MOCK_AUTH_URL = "http://mastodon.example/oauth_mock"
DEFAULT_CONNECTION_NAME = "mouf"


class UserMastodonSourceAddTest(TestCase):
  """Test addition of a mastodon feed.
  """
  
  def add_request(self, username, optionsDict, expectedStatusCode=302):
    """
    Send the request as a JSON loaded POST (a redirect is expected
    in case of success).
    """
    resp = self.client.post(reverse("user_tributary_mastodon_add",
                                      kwargs={"owner_name":username}),
                              optionsDict)
    self.assertEqual(expectedStatusCode,resp.status_code, resp.content)
    return resp

  def setUp(self):
    self.date = datetime.now(timezone.utc)
    self.user = User.objects.create_user(username="uA",
                                         password="pA")
    self.user_profile = UserProfile.objects.create(owner=self.user)
    self.other_user = User.objects.create_user(username="uB",
                                               password="pB")
    self.other_profile = UserProfile.objects.create(owner=self.other_user)


  def _default_mock_setup(
      self,
      mocked_register_application_on_instance):
    mocked_register_application_on_instance.return_value = RegistrationInfo(
        MOCK_CLIENT_ID,
        MOCK_CLIENT_SECRET,
        MOCK_VAPID_KEY)
  
  @mock.patch('wom_tributary.utils.mastodon_oauth.register_application_on_instance')
  def test_add_new_feed_source_to_owner_with_instance_registration_success(
      self,
      mocked_register_application_on_instance):
  
    self._default_mock_setup(mocked_register_application_on_instance)
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    new_timeline_instance = DEFAULT_INSTANCE
    new_timeline_title = "a new"
    self.add_request("uA",
                     {"instance_url": new_timeline_instance,
                      "title": new_timeline_title})

    self.assertEqual(
        new_timeline_instance,
        mocked_register_application_on_instance.call_args[0][0]
        )
    self.assertEqual(1,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    added_source = self.user_profile.sources.get()
    self.assertEqual(MastodonTimeline.SOURCE_NAME, added_source.title)
    self.assertEqual(added_source.url, new_timeline_instance)
    added_feed = GeneratedFeed.objects.get(source=added_source)
    self.assertEqual(new_timeline_title, added_feed.title)
    added_timeline = MastodonTimeline.objects.get(generated_feed=added_feed)
    added_registration_info = added_timeline.mastodon_user_access_info.application_registration_info
    self.assertEqual(added_registration_info.instance_url,
                     new_timeline_instance)
    self.assertEqual(added_registration_info.client_id,
                     MOCK_CLIENT_ID)
    self.assertEqual(added_registration_info.client_secret,
                     MOCK_CLIENT_SECRET)
    self.assertEqual(added_registration_info.validation_key,
                     MOCK_VAPID_KEY)


  @mock.patch('wom_tributary.utils.mastodon_oauth.register_application_on_instance')
  def test_add_new_feed_source_to_owner_with_instance_registration_failing_registration(
      self,
      mocked_register_application_on_instance):
    mock_error_message = "Connection error"
    self._default_mock_setup(mocked_register_application_on_instance)
    mocked_register_application_on_instance.side_effect = RuntimeError(mock_error_message)
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    new_timeline_instance = DEFAULT_INSTANCE
    new_timeline_title = "a new"
    response = self.add_request(
        "uA",
        {"instance_url": new_timeline_instance,
         "title": new_timeline_title},
        expectedStatusCode=200)
    page_content = response.content.decode("utf-8")
    self.assertTrue(mock_error_message in page_content,
                    page_content)
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())

  @mock.patch('wom_tributary.utils.mastodon_oauth.register_application_on_instance')
  def test_add_new_feed_source_to_other_user_fails(self,
      mocked_register_application_on_instance):
    self._default_mock_setup(mocked_register_application_on_instance)
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    new_timeline_instance = DEFAULT_INSTANCE
    new_timeline_title = "a new"
    self.add_request("uB",
                       {"instance_url": new_timeline_instance,
                    "title": new_timeline_title},
                expectedStatusCode=403)

  @mock.patch('wom_tributary.utils.mastodon_oauth.register_application_on_instance')
  def test_add_same_timeline_fails(self,
      mocked_register_application_on_instance):
    self._default_mock_setup(mocked_register_application_on_instance)
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    new_timeline_instance = DEFAULT_INSTANCE
    new_timeline_title = "a new"
    self.add_request("uA",
                     {"instance_url": new_timeline_instance,
                      "title": new_timeline_title})
    response = self.add_request(
        "uA",
        {"instance_url": new_timeline_instance,
         "title": new_timeline_title},
        expectedStatusCode = 200)
    page_content = response.content.decode("utf-8")
    self.assertTrue(
        "A feed with the same title exists for the same instance." in page_content,
        page_content)
    
  @mock.patch('wom_tributary.utils.mastodon_oauth.register_application_on_instance')
  def test_add_second_timeline_from_same_instance(
      self,
      mocked_register_application_on_instance):
    self._default_mock_setup(mocked_register_application_on_instance)
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    new_timeline_instance = DEFAULT_INSTANCE
    new_timeline_title = "a new"
    self.add_request("uA",
                     {"instance_url": new_timeline_instance,
                      "title": new_timeline_title})
    second_timeline_instance = DEFAULT_INSTANCE
    second_timeline_title = "another new"
    self.add_request("uA",
                     {"instance_url": second_timeline_instance,
                      "title": second_timeline_title})
    self.assertEqual(1,self.user_profile.sources.count())
    self.assertEqual(1, Reference.objects.filter(
      url=DEFAULT_INSTANCE,
      title=MastodonTimeline.SOURCE_NAME).count())
    self.assertEqual(2, MastodonTimeline.objects.count())
  

class MastodonAuthPageTest(TestCase):
  
    def setUp(self):
        self.stub_date = datetime.now(timezone.utc)
        self.source = Reference.objects.create(
            url="http://glop",
            title="glop",
            pub_date=self.stub_date)
        self.user = User.objects.create_user(
            username="uA", password="pA"
            )        

    def _get(self, request_params=None):
        request_params = request_params or {}
        # login as uA and make sure it succeeds
        self.assertTrue(
            self.client.login(username="uA",password="pA"))
        # send the request
        return self.client.get(
            reverse("user_tributary_mastodon",
                        kwargs={"owner_name":"uA"}),
            request_params)

    def _generate_userprofile_with_mastodon_access_info(self, num_timelines):
      app_reg = MastodonApplicationRegistration.objects.create(instance_url=DEFAULT_INSTANCE)
      app_reg.save()
      access_info = MastodonUserAccessInfo.objects.create(application_registration_info=app_reg)
      access_info.save()
      profile = UserProfile.objects.create(owner = self.user)
      for i in range(num_timelines):
        feed = GeneratedFeed.objects.create(
            provider="M", source=self.source, title=DEFAULT_CONNECTION_NAME,
            last_update_check=self.stub_date)
        MastodonTimeline.objects.create(
            generated_feed=feed,
            mastodon_user_access_info=access_info)
        profile.generated_feeds.add(feed)
      profile.save()
      return profile, access_info
      
    def test_without_timeline_nor_mastodon_info_template_context_has_no_info(self):
      UserProfile.objects.create(owner=self.user)
      resp = self._get()
      self.assertEqual(200, resp.status_code)
      connection_statuses = resp.context["mastodon_connection_status_list"]
      self.assertEqual(0, len(connection_statuses))

    @mock.patch('wom_tributary.utils.mastodon_oauth.try_get_authorized_client_and_token')
    @mock.patch('wom_tributary.utils.mastodon_oauth.generate_authorization_url')
    def test_with_mastodon_info_but_no_auth_template_context_has_auth_link(self,
            mocked_generate_auth_url,
            mocked_try_get_authorized_client_and_token):
      mocked_try_get_authorized_client_and_token.return_value = None
      mocked_generate_auth_url.return_value = MOCK_AUTH_URL
      self._generate_userprofile_with_mastodon_access_info(1)
      resp = self._get()
      self.assertEqual(200, resp.status_code)
      connection_statuses = resp.context["mastodon_connection_status_list"]
      self.assertEqual(1, len(connection_statuses))
      connection = connection_statuses[0]
      self.assertEqual(False, connection.auth_status.is_auth)
      self.assertEqual(MOCK_AUTH_URL,
                       connection.auth_status.auth_url)

    @mock.patch('wom_tributary.utils.mastodon_oauth.try_get_authorized_client_and_token')
    @mock.patch('wom_tributary.utils.mastodon_oauth.generate_authorization_url')
    def test_when_authorized_context_has_no_auth_link(self,
            mocked_generate_auth_url,
            mocked_try_get_authorized_client_and_token):
      client_mock = mock.MagicMock()
      client_mock.is_auth = False
      mocked_try_get_authorized_client_and_token.return_value = (client_mock, "mock_token")
      mocked_generate_auth_url.return_value = MOCK_AUTH_URL
      self._generate_userprofile_with_mastodon_access_info(1)
      resp = self._get()
      self.assertEqual(200, resp.status_code)
      connection_statuses = resp.context["mastodon_connection_status_list"]
      self.assertEqual(1, len(connection_statuses))
      connection = connection_statuses[0]
      self.assertEqual(True, connection.auth_status.is_auth)
      self.assertEqual(None, connection.auth_status.auth_url)
        
    @mock.patch('wom_tributary.utils.mastodon_oauth.try_get_authorized_client_and_token')
    @mock.patch('wom_tributary.utils.mastodon_oauth.generate_authorization_url')
    def test_with_timelines_template_context_has_correct_info(self,
            mocked_generate_auth_url,
            mocked_try_get_authorized_client_and_token):
      client_mock = mock.MagicMock()
      client_mock.get_activities.return_value = [1,2,3]
      mocked_try_get_authorized_client_and_token.return_value = (client_mock, "mock_token")
      mocked_generate_auth_url.return_value = MOCK_AUTH_URL
      profile, info = self._generate_userprofile_with_mastodon_access_info(2)
      resp = self._get()
      self.assertEqual(200, resp.status_code)
      connection_statuses = resp.context["mastodon_connection_status_list"]
      self.assertEqual(2, len(connection_statuses))
      connection = connection_statuses[0]
      self.assertEqual(True, connection.auth_status.is_auth)
      self.assertEqual(None, connection.auth_status.auth_url)
      timeline_info = connection.timeline_info
      self.assertTrue(timeline_info.fetchable)
      connection = connection_statuses[1]
      self.assertEqual(True, connection.auth_status.is_auth)
      self.assertEqual(None, connection.auth_status.auth_url)
      timeline_info = connection.timeline_info
      self.assertTrue(timeline_info.fetchable)
      
        
    @mock.patch('wom_tributary.utils.mastodon_oauth.try_get_authorized_client_and_token')
    @mock.patch('wom_tributary.utils.mastodon_oauth.generate_authorization_url')
    def test_with_timelines_try_get_authorized_client_and_token_called_with_right_token(self,
            mocked_generate_auth_url,
            mocked_try_get_authorized_client_and_token):
      client_mock = mock.MagicMock()
      client_mock.get_activities.return_value = [1]
      token_param_name = 'oauth_verifier'
      token_verifier = "MASTO_TKV"
      def assert_expected_token(request_params, session, instance_url, redirect_uri, user_info):
        self.assertEqual(token_verifier,
                         request_params.get(token_param_name))
        self.assertEqual(DEFAULT_INSTANCE, instance_url)
      mocked_try_get_authorized_client_and_token.return_value = (client_mock, "mock_token")
      mocked_try_get_authorized_client_and_token.side_effect = assert_expected_token
      mocked_generate_auth_url.return_value = MOCK_AUTH_URL
      profile, info = self._generate_userprofile_with_mastodon_access_info(2)
      resp = self._get({token_param_name: token_verifier})
      self.assertEqual(200, resp.status_code)
