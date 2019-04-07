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

import mock

from datetime import datetime
from django.utils import timezone

from django.core.urlresolvers import reverse

from django.test import TestCase

from wom_pebbles.models import Reference

from wom_user.models import UserProfile


from wom_tributary.models import TwitterTimeline
from wom_tributary.models import GeneratedFeed
from wom_tributary.models import TwitterUserInfo

from django.contrib.auth.models import User


class UserTwitterSourceAddTest(TestCase):
  """Test addition of a twitter feed.
  """
  
  def add_request(self, username, optionsDict, expectedStatusCode=302):
    """
    Send the request as a JSON loaded POST (a redirect is expected
    in case of success).
    """
    resp = self.client.post(reverse("wom_user.views.user_tributary_twitter_add",
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

  def test_add_new_feed_source_to_owner(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    new_timeline_user = u"joe"
    new_timeline_title = u"a new"
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "title": new_timeline_title})
    self.assertEqual(1,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    added_source = self.user_profile.sources.get()
    self.assertEqual(TwitterTimeline.SOURCE_NAME, added_source.title)
    self.assertEqual(TwitterTimeline.SOURCE_URL, added_source.url)
    added_feed = GeneratedFeed.objects.get(source=added_source)
    self.assertEqual(new_timeline_title, added_feed.title)
    added_timeline = TwitterTimeline.objects.get(generated_feed=added_feed)
    self.assertEqual(new_timeline_user, added_timeline.username)
    
  def test_add_new_feed_source_to_other_user_fails(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    new_timeline_user = u"joe"
    new_timeline_title = u"a new"
    self.add_request("uB",
                       {"username": new_timeline_user,
                    "title": new_timeline_title},
                expectedStatusCode=403)

  def test_add_timeline_that_already_exists(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    new_timeline_user = u"joe"
    new_timeline_title = u"a new"
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "title": new_timeline_title})
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "title": new_timeline_title})
    self.assertEqual(1, self.user_profile.sources.count())
    self.assertEqual(0, self.user_profile.web_feeds.count())
    self.assertEqual(1, TwitterTimeline.objects.filter(
      username=new_timeline_user).count())
    
  def test_add_second_timeline(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    new_timeline_user = u"joe"
    new_timeline_title = u"a new"
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "title": new_timeline_title})
    second_timeline_user = u"bill"
    second_timeline_title = u"another new"
    self.add_request("uA",
                     {"username": second_timeline_user,
                      "title": second_timeline_title})
    self.assertEqual(1,self.user_profile.sources.count())
    self.assertEqual(1, Reference.objects.filter(
      url=TwitterTimeline.SOURCE_URL,
      title=TwitterTimeline.SOURCE_NAME).count())
    self.assertEqual(2, TwitterTimeline.objects.count())
  

class TwitterAuthPageTest(TestCase):
  
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
            reverse("wom_user.views.user_tributary_twitter",
                        kwargs={"owner_name":"uA"}),
            request_params)

    def _generate_timelines(self, num_timelines):
        tw_uname = "mouf"
        info = TwitterUserInfo.objects.create(username=tw_uname)
        p = UserProfile.objects.create(
            owner = self.user,
            twitter_info = info)
        for i in range(num_timelines):
            feed = GeneratedFeed.objects.create(
                provider="T", source=self.source, title=str(i),
                last_update_check=self.stub_date)
            TwitterTimeline.objects.create(
                username=tw_uname,
                generated_feed=feed)
            p.generated_feeds.add(feed)
        p.save()
    
    def test_without_timeline_not_twitter_info_context_has_no_info(self):
        UserProfile.objects.create(owner=self.user)
        
        resp = self._get()
        self.assertEqual(200, resp.status_code)
        oauth_status = resp.context["twitter_oauth_status"]
        self.assertEqual(None, oauth_status)
        summary = resp.context["twitter_timelines_recap"]
        self.assertEqual(None, summary)

    @mock.patch('wom_tributary.utils.twitter_oauth.try_get_authorized_client')
    @mock.patch('wom_tributary.utils.twitter_oauth.generate_authorization_url')
    def test_with_twitter_info_but_no_auth_context_has_auth_link(self,
            mocked_generate_auth_url,
            mocked_try_get_auth_client):        
        mocked_try_get_auth_client.return_value = None
        mocked_generate_auth_url.return_value = "http://birdsite"
        
        info = TwitterUserInfo.objects.create(username="mouf")
        UserProfile.objects.create(
            owner = self.user,
            twitter_info = info)
        
        resp = self._get()
        self.assertEqual(200, resp.status_code)
        oauth_status = resp.context["twitter_oauth_status"]
        self.assertEqual(False, oauth_status.is_auth)
        self.assertEqual(mocked_generate_auth_url.return_value,
                             oauth_status.auth_url)

    @mock.patch('wom_tributary.utils.twitter_oauth.try_get_authorized_client')
    @mock.patch('wom_tributary.utils.twitter_oauth.generate_authorization_url')
    def test_when_authorized_context_has_no_auth_link(self,
            mocked_generate_auth_url,
            mocked_try_get_auth_client):
        mocked_try_get_auth_client.return_value = True
        mocked_generate_auth_url.return_value = "http://birdsite"
        info = TwitterUserInfo.objects.create(username="mouf")
        UserProfile.objects.create(
            owner = self.user,
            twitter_info = info)
        resp = self._get()
        self.assertEqual(200, resp.status_code)
        oauth_status = resp.context["twitter_oauth_status"]
        self.assertEqual(True, oauth_status.is_auth)
        self.assertEqual(None, oauth_status.auth_url)
        
    @mock.patch('wom_tributary.utils.twitter_oauth.try_get_authorized_client')
    @mock.patch('wom_tributary.utils.twitter_oauth.generate_authorization_url')
    def test_with_timelines_when_authorized_context_has_no_auth_link(self,
            mocked_generate_auth_url,
            mocked_try_get_auth_client):
        client_mock = mock.MagicMock()
        client_mock.get_activities.return_value = [1,2,3]
        mocked_try_get_auth_client.return_value = client_mock
        mocked_generate_auth_url.return_value = "http://birdsite"

        self._generate_timelines(2)
        
        resp = self._get()
        self.assertEqual(200, resp.status_code)
        oauth_status = resp.context["twitter_oauth_status"]
        self.assertEqual(True, oauth_status.is_auth)
        self.assertEqual(None, oauth_status.auth_url)
        summary = resp.context["twitter_timelines_recap"]
        self.assertEqual(2, len(summary))
        self.assertTrue(summary[0].fetchable)
        self.assertTrue(summary[1].fetchable)
        
    @mock.patch('wom_tributary.utils.twitter_oauth.try_get_authorized_client')
    @mock.patch('wom_tributary.utils.twitter_oauth.generate_authorization_url')
    def test_with_timelines_when_get_has_oauth_token_it_is_passed_to_try_get_authorized_client(self,
            mocked_generate_auth_url,
            mocked_try_get_auth_client):
        
        client_mock = mock.MagicMock()
        client_mock.get_activities.return_value = [1]

        token_param_name = 'oauth_verifier'
        token_verifier = "BIRD_TKV"
        def side_effect(request_params, session, user_info):
            self.assertEqual(token_verifier,
                        request_params.get(token_param_name))
        mocked_try_get_auth_client.return_value = client_mock
        mocked_try_get_auth_client.side_effect = side_effect
        mocked_generate_auth_url.return_value = "http://birdsite"
        
        self._generate_timelines(1)
        
        resp = self._get({token_param_name: token_verifier})
        self.assertEqual(200, resp.status_code)
