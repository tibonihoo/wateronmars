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

import json

from datetime import datetime
from datetime import timedelta
from django.utils import timezone

from django.urls import reverse

from django.test import TestCase

from wom_user.models import UserProfile
from wom_user.models import ReferenceUserStatus

from wom_pebbles.models import Reference

from wom_river.models import (
    WebFeed,
    WebFeedCollation
    )

from wom_user.views import MAX_ITEMS_PER_PAGE
from wom_user.settings import (
    WEB_FEED_COLLATION_TIMEOUT,
    WEB_FEED_COLLATION_MIN_NUM_REF_TARGET,
    WEB_FEED_COLLATION_MAX_NUM_REF_TARGET
    )

from wom_user.tasks import check_user_unread_feed_items

from django.contrib.auth.models import User


class UserSieveViewTest(TestCase):

    def setUp(self):
        # Create 2 users and 3 sources (1 exclusive to each and a
        # shared one) with more references than MAX_ITEM_PER_PAGE
        self.user1 = User.objects.create_user(username="uA",password="pA")
        user1_profile = UserProfile.objects.create(owner=self.user1)
        self.user2 = User.objects.create_user(username="uB",password="pB")
        user2_profile = UserProfile.objects.create(owner=self.user2)
        date = datetime.now(timezone.utc)
        self.s1 = Reference.objects.create(url="http://mouf",title="glop",pub_date=date)
        f1 = WebFeed.objects.create(xmlURL="http://mouf/rss.xml",
                                    last_update_check=date,
                                    source=self.s1)
        # Having a second feed for a same source caused a bug in
        # ReferenceUserStatus creation when collecting new References
        f1Category = WebFeed.objects.create(xmlURL="http://mouf/category/rss.xml",
                                            last_update_check=date,
                                            source=self.s1)
        self.s2 = Reference.objects.create(url="http://bla",title="bla",pub_date=date)
        f2 = WebFeed.objects.create(xmlURL="http://bla/rss.xml",
                                    last_update_check=date,
                                    source=self.s2)
        self.s3 = Reference.objects.create(url="http://greuh",title="greuh",pub_date=date)
        f3 = WebFeed.objects.create(xmlURL="http://greuh/rss.xml",
                                    last_update_check=date,
                                    source=self.s3)
        user1_profile.web_feeds.add(f1)
        user1_profile.web_feeds.add(f1Category)
        user1_profile.web_feeds.add(f3)
        user1_profile.sources.add(self.s1,self.s3)
        user2_profile.web_feeds.add(f2)
        user2_profile.web_feeds.add(f3)
        user2_profile.sources.add(self.s2,self.s3)
        self.num_items_per_source = MAX_ITEMS_PER_PAGE+1
        for i in range(self.num_items_per_source):
            date += timedelta(hours=1)
            if i==0:
              r = Reference.objects.create(url="http://r1",title="s1r%d" % i,
                                           pub_date=date)#,source=s1
              r.sources.add(self.s1)
              r = Reference.objects.create(url="http://r2",title="s2r%d" % i,
                                           pub_date=date)#,source=s2
              r.sources.add(self.s2)
              r = Reference.objects.create(url="http://r3",title="s3r%d" % i,
                                           pub_date=date)#,source=s3
              r.sources.add(self.s3)
            else:
              r = Reference.objects.create(url="http://r1%d" % i,title="s1r%d" % i,
                                           pub_date=date)#,source=s1
              r.sources.add(self.s1)
              r = Reference.objects.create(url="http://r2%d" % i,title="s2r%d" % i,
                                           pub_date=date)#,source=s2
              r.sources.add(self.s2)
              r = Reference.objects.create(url="http://r3%d" % i,title="s3r%d" % i,
                                           pub_date=date)#,source=s3
              r.sources.add(self.s3)


    def test_check_user_unread_feed_items(self):
      """Test that that unread items are correctly collected: just the
      right number and correctly saved in DB.
      """
      count = check_user_unread_feed_items(self.user1)
      self.assertEqual(2*self.num_items_per_source,count)
      self.assertEqual(count,ReferenceUserStatus.objects\
                       .filter(owner=self.user1).count())

    def test_check_user_unread_feed_items_with_collations(self):
      """Test that that unread items are correctly collected
      when they are all set for collations.
      """
      user1_profile = UserProfile.objects.filter(owner=self.user1).get()
      user1_feeds = list(user1_profile.web_feeds.all())
      last_processing_date = datetime.now(timezone.utc)- 2*WEB_FEED_COLLATION_TIMEOUT
      for f in user1_feeds:
        print("Setting collation for ", f)
        collating_feed = WebFeedCollation.objects.create(
            feed=f,
            last_completed_collation_date=last_processing_date)
        user1_profile.collating_feeds.add(collating_feed)
      count = check_user_unread_feed_items(self.user1)
      # The exact number of generated refs depends on the capping on
      # the number of rereferences allowed to be collated in a same
      # item as well as some time span conditions which makes it
      # complicated to get the exact number, and a bit useless a this
      # stage, so we're just checking the ballpark.
      total_items = (len(user1_feeds) * self.num_items_per_source)
      expected_count = ( total_items / WEB_FEED_COLLATION_MAX_NUM_REF_TARGET)
      self.assertEqual(expected_count // 10, count // 10)
      
    def test_get_html_for_owner_returns_max_items_ordered_oldest_first(self):
        """
        Make sure a user can see its river properly ordered
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uA's river
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(200,resp.status_code)
        self.assertIn("sieve.html",[t.name for t in resp.templates])
        self.assertIn("source_add_bookmarklet", resp.context)
        self.assertIn("user_collection_url", resp.context)
        self.assertIn("oldest_unread_references", resp.context)
        items = resp.context["oldest_unread_references"]
        self.assertGreaterEqual(MAX_ITEMS_PER_PAGE,len(items))
        self.assertEqual((False,),tuple(set([r.has_been_read for r in items])))
        rustTitles = set([int(r.reference.title[1]) for r in items])
        self.assertEqual(rustTitles,set((1,3)))
        referenceNumbers = [int(r.reference.title[3:]) for r in items]
        self.assertEqual(list(sorted(referenceNumbers)),referenceNumbers)
        for rust in items:
          expected_source = getattr(self,"s%d" % int(rust.reference.title[1]))
          self.assertEqual(expected_source,rust.main_source,"Wrong main source for %s" % rust)

    def test_get_html_for_non_owner_logged_user_is_forbidden(self):
        """
        Make sure a logged in user can see another user's river.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # request uB's river
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uB"}))
        self.assertEqual(403,resp.status_code)

    def test_get_html_for_anonymous_redirects_to_login(self):
        """
        Make sure an anonymous (ie. not logged) user can see a user's river.
        """
        # request uA's river without loging in.
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        self.assertEqual(302,resp.status_code)
        self.assertRegex(
            resp["Location"],
            reverse('user_login')
            + "\\?next="
            + reverse("user_river_sieve",
                          kwargs={"owner_name":"uA"}))

    def test_post_json_pick_item_out_of_sieve(self):
        """
        Make sure posting an item as read will remove it from the sieve.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # check presence of r1 reference
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        num_ref_r1 = [r.reference.url for r in items].count("http://r1")
        self.assertLessEqual(1,num_ref_r1)
        # mark the first reference as read.
        resp = self.client.post(reverse("user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                json.dumps({"action":"read","references":["http://r1"]}),
                                content_type="application/json")
        self.assertEqual(200,resp.status_code)
        resp_dic = json.loads(resp.content)
        self.assertEqual("read",resp_dic["action"])
        self.assertEqual("success",resp_dic["status"])
        self.assertLessEqual(num_ref_r1,resp_dic["count"])
        # check absence of r1 reference
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        self.assertEqual(0,[r.reference.url for r in items].count("http://r1"))

    def test_post_json_pick_several_items_out_of_sieve(self):
        """
        Make sure posting a list of items as read will remove them from the sieve.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # check presence of r1 reference
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        num_ref_r1 = [r.reference.url for r in items].count("http://r1")
        self.assertLessEqual(1,num_ref_r1)
        num_ref_r3 = [r.reference.url for r in items].count("http://r3")
        self.assertLessEqual(1,num_ref_r3)
        # mark the first reference as read.
        resp = self.client.post(reverse("user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                json.dumps({"action":"read",
                                                  "references":["http://r1","http://r3"]}),
                                content_type="application/json")
        self.assertEqual(200,resp.status_code)
        resp_dic = json.loads(resp.content)
        self.assertEqual("read",resp_dic["action"])
        self.assertEqual("success",resp_dic["status"])
        self.assertLessEqual(num_ref_r1+num_ref_r3,resp_dic["count"])
        # check absence of r1 reference
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        self.assertEqual(0,[r.reference.url for r in items].count("http://r1"))
        self.assertEqual(0,[r.reference.url for r in items].count("http://r3"))

    def test_post_json_drop_sieve_content(self):
        """
        Make sure posting an item as read will remove it from the sieve.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # check presence of r1 reference
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        num_refs = len(items)
        self.assertGreaterEqual(num_refs, 1)
        # mark the first reference as read.
        resp = self.client.post(reverse("user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                json.dumps({"action":"drop"}),
                                content_type="application/json")
        self.assertEqual(200,resp.status_code)
        resp_dic = json.loads(resp.content)
        self.assertEqual("drop",resp_dic["action"])
        self.assertEqual("success",resp_dic["status"])
        self.assertLessEqual(num_refs,resp_dic["count"])
        # check emptyness of sieve
        resp = self.client.get(reverse("user_river_sieve",
                                       kwargs={"owner_name":"uA"}))
        items = resp.context["oldest_unread_references"]
        self.assertEqual(0,len(items))

    def test_post_malformed_json_returns_error(self):
        """
        Make sure when the json is malformed an error that is not a server error is returned.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # mark a of uB reference as read.
        resp = self.client.post(reverse("user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                "action=read,references=(http://r1)",
                                content_type="application/json")
        self.assertEqual(400,resp.status_code)

    def test_post_json_for_non_owner_logged_user_is_forbidden(self):
        """
        Make sure when the json is malformed an error that is not a server error is returned.
        """
        # login as uA and make sure it succeeds
        self.assertTrue(self.client.login(username="uA",password="pA"))
        # mark a of uB reference as read.
        resp = self.client.post(reverse("user_river_sieve",
                                        kwargs={"owner_name":"uB"}),
                                json.dumps({"action":"read","references":["http://r2"]}),
                                content_type="application/json")
        self.assertEqual(403,resp.status_code)

    def test_post_json_for_anonymous_redirects(self):
        """
        Make sure an anonymous (ie. not logged) user can see a user's river.
        """
        resp = self.client.post(reverse("user_river_sieve",
                                        kwargs={"owner_name":"uA"}),
                                json.dumps({"action":"read","references":["http://r1"]}),
                                content_type="application/json")
        self.assertEqual(302,resp.status_code)

