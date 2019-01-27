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

from datetime import datetime
from django.utils import timezone

from django.core.urlresolvers import reverse

from django.test import TestCase

from wom_pebbles.models import Reference

from wom_user.models import UserProfile


from wom_tributary.models import TwitterTimeline
from wom_tributary.models import GeneratedFeed

from django.contrib.auth.models import User


# TODO:
# - test twitter
# - add got_authorized flag to twitter timeline model
# - add "twitter check" page as landing page for addition and auth

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
    new_timeline_kind = unicode(TwitterTimeline.HOME_TIMELINE)
    new_timeline_title = u"a new"
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "kind": new_timeline_kind,
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
    self.assertEqual(new_timeline_kind, added_timeline.kind)    
    # TODO: test got_auth = False
    
  def test_add_new_feed_source_to_other_user_fails(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    self.assertEqual(0,self.user_profile.sources.count())
    self.assertEqual(0,self.user_profile.web_feeds.count())
    new_timeline_user = u"joe"
    new_timeline_kind = unicode(TwitterTimeline.HOME_TIMELINE)
    new_timeline_title = u"a new"
    self.add_request("uB",
                       {"username": new_timeline_user,
                         "kind": new_timeline_kind,
                    "title": new_timeline_title},
                expectedStatusCode=403)

  def test_add_timeline_that_already_exists(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    new_timeline_user = u"joe"
    new_timeline_kind = unicode(TwitterTimeline.HOME_TIMELINE)
    new_timeline_title = u"a new"
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "kind": new_timeline_kind,
                      "title": new_timeline_title})
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "kind": new_timeline_kind,
                      "title": new_timeline_title})
    self.assertEqual(1, self.user_profile.sources.count())
    self.assertEqual(0, self.user_profile.web_feeds.count())
    self.assertEqual(1, TwitterTimeline.objects.filter(
      username=new_timeline_user,
      kind=new_timeline_kind).count())
    
  def test_add_second_timeline(self):
    # login as uA and make sure it succeeds
    self.assertTrue(self.client.login(username="uA",
                      password="pA"))
    new_timeline_user = u"joe"
    new_timeline_kind = unicode(TwitterTimeline.HOME_TIMELINE)
    new_timeline_title = u"a new"
    self.add_request("uA",
                     {"username": new_timeline_user,
                      "kind": new_timeline_kind,
                      "title": new_timeline_title})
    second_timeline_user = u"bill"
    second_timeline_kind = unicode(TwitterTimeline.HOME_TIMELINE)
    second_timeline_title = u"another new"
    self.add_request("uA",
                     {"username": second_timeline_user,
                      "kind": second_timeline_kind,
                      "title": second_timeline_title})
    self.assertEqual(1,self.user_profile.sources.count())
    self.assertEqual(1, Reference.objects.filter(
      url=TwitterTimeline.SOURCE_URL,
      title=TwitterTimeline.SOURCE_NAME).count())
    self.assertEqual(2, TwitterTimeline.objects.count())
  
